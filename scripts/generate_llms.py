#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Generate llms.txt, the per-area shards and llms-full.txt.

llms.txt is the structured, LLM-oriented summary of the project: what it is,
how to install and use it, and where every documentation page lives.

The page list used to be a literal table maintained by hand. It was written
when the project was a fractional octave filter bank and it was never extended
as the library grew, so it ended up naming 42 of 221 English pages: whole
domains the front page advertises (aircraft noise, underwater propagation, FDTD
simulation, the entire API reference) were invisible to anything reading it,
and the summary still described a filter bank. The list is derived from the
site now, and a page that cannot be placed stops the run, so the same drift
cannot happen quietly again.

Every page comes from the site itself. ``site/scripts/agent-md.mjs --dump``
writes the routes of the English site (``routes.json``: each page's kind,
title, description and the standards it implements) and the Markdown copy of
every page these files carry, the same copy the site publishes beside the
page at ``<page>/index.md``. This script reads that dump (``--pages``) and
nothing else of the pages: the hand-written mirror under ``docs/``, which
these files used to be cut from, said less than the site and named its pages
otherwise.

Three kinds of artifact are produced:

``llms.txt``
    The index. Every English page of the site, grouped by area and each with
    what its own description says it is about, plus the evidence pages, one
    line per errata family with its entry count and per published catalogue
    with its row count, where the Markdown copies are, the Spanish tree and
    the API reference as an Optional section. Every English page is linked
    (see :func:`_check_index_covers_the_site`).
    Committed, and dateless, so that it changes only when the site does
    (``make llms``).
``llms/llms-<area>.txt``
    One shard per documented area, each small enough to survive a single fetch,
    plus one for the conformance report, one set for the errata register and one
    per published catalogue. ``llms-full.txt`` is several megabytes, so a client
    that truncates at a few hundred kilobytes (most of them do) reads the first
    few metrology guides and nothing else, which is the worst possible sample:
    it looks like the old narrow library. A shard too long for one fetch
    travels in numbered parts instead, ``llms-<area>-1.txt``,
    ``llms-<area>-2.txt`` and so on (see :func:`_shard_parts`).
``llms-full.txt``
    The complete concatenation, kept for clients that can take it.

Each page in a shard and in ``llms-full.txt`` is its Markdown copy, byte for
byte, header included: the header says where the page lives, for which
release, by whom, when, and against which standards, so a passage read from a
shard can be cited and dated. The header carries the dates the page was
published and last changed, and a committed file cannot carry the date of the
commit that commits it, so the shards and ``llms-full.txt`` are not committed:
the site build writes them (``--build``, run by ``site/package.json``
``prebuild``) into ``site/public/``, which the build publishes, and the check
of the Markdown copies (``site/scripts/check-markdown-twins.mjs``) holds every
page they carry to its copy. Where a shard is cut does not depend on the
dates, so the ``llms.txt`` that ``make llms`` writes from a dump without them
names the same files the build writes.
"""

from __future__ import annotations

import argparse
import dataclasses
import functools
import json
import pathlib
import re
import subprocess
import tomllib
from typing import TYPE_CHECKING

from generate_site_reports import family_pages
from markdown_fences import code_lines
from markdown_spans import page_markup

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from generate_site_reports import FamilyPage

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


@functools.cache
def _ignored_paths() -> frozenset[str]:
    """Everything under :data:`DOCS` that git ignores, as repo-relative paths.

    Nothing for a :data:`DOCS` outside the repository, as the tests point it
    at a tree of their own: git ignores no file there, and the repository's
    listing names other files. The names are read as git writes them with
    ``-z``, whole, where a plain listing quotes a name that holds a character
    outside ASCII.
    """
    if not DOCS.is_relative_to(ROOT):
        return frozenset()
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
            "--",
            DOCS.relative_to(ROOT).as_posix(),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        check=False,
    )
    return frozenset(name for name in result.stdout.split("\0") if name)


def _git_ignored(path: pathlib.Path) -> bool:
    """Is this page of the mirror one git ignores (a local plan, a scratch note)?

    The page is named as :func:`_ignored_paths` lists it, by its path in the
    repository; a page outside the repository is one git ignores nothing of.
    """
    if not path.is_relative_to(ROOT):
        return False
    return path.relative_to(ROOT).as_posix() in _ignored_paths()


def _shown(path: pathlib.Path) -> pathlib.Path:
    """*path* as a message names it: relative to the repository, or whole when it lies outside, as a tree of a test's own does."""
    return path.relative_to(ROOT) if path.is_relative_to(ROOT) else path


CONTENT = ROOT / "site" / "src" / "content" / "docs"
#: Where the site build publishes the llms files from: everything under
#: site/public is served verbatim at the site root.
PUBLIC = ROOT / "site" / "public"
#: Where the per-area shards are written by ``--build``, so they publish at
#: /llms/llms-<area>.txt and the site root keeps exactly llms.txt and
#: llms-full.txt.
SHARDS_DIR = PUBLIC / "llms"
#: The dump ``site/scripts/agent-md.mjs --dump`` writes, read by default.
PAGES = ROOT / "build" / "agent-md"
#: The committed index ``make llms`` writes.
INDEX = ROOT / "llms.txt"
SITE_URL = "https://docs.jmrp.io/phonometry"
REPO_URL = "https://github.com/jmrplens/phonometry"

#: The hand-written table of every public name, which only docs/ holds.
QUICK_API_TABLE = "docs/reference/api/index.md"
DOI = "10.5281/zenodo.21215280"

#: Shard budget. Comfortably under the truncation limit of the AI fetch tools
#: that cap response size, with room for a page to grow. Enforced: main() exits
#: non-zero if a shard is over it (see :func:`_check_shard_budget`). A shard
#: exactly at the limit passes; only strictly over fails, both here and in the
#: message it raises. A shard over it is cut into parts rather than refused
#: (see :func:`_shard_parts`).
SHARD_LIMIT_BYTES = 200_000

#: The budget of ``llms.txt`` itself. It lists every English page with what
#: the page is about, the errata by source and the catalogues, and an index is
#: read whole: it is fetched first, by clients that cut a response at a few
#: hundred kilobytes, and a cut index loses the end of its list without saying
#: so. Enforced as the shards are (see :func:`_check_index_budget`).
LLMS_TXT_LIMIT_BYTES = 200_000

#: The data every catalogue page tables, written by
#: ``scripts/generate_catalogue_data.py`` and committed.
CATALOGUE_DATA = ROOT / "site" / "src" / "generated" / "catalogues.mjs"

#: The title of the upgrade guide's shard, in its head and in the index.
UPGRADING_TITLE = "Upgrading from 3.3 to 4.0"

#: The glossary page, which has a shard of its own (see :func:`_shard_plan`).
GLOSSARY_ROUTE = "reference/glossary"

#: The conformance report, which has a shard of its own: at more than 400 kB
#: it is cut into parts at its sections, one per domain.
CONFORMANCE_ROUTE = "reference/conformance"

#: The index of the errata register, which opens the register's shard.
ERRATA_ROUTE = "reference/errata"

#: The index of the published catalogues, which links one page per catalogue.
CATALOGUES_ROUTE = "reference/catalogues"


#: The bibliography, which has a shard of its own (see :func:`build_shards`).
BIBLIOGRAPHY_ROUTE = "reference/bibliography"

#: Markdown files under docs/ that are not documentation pages.
NOT_PAGES = frozenset({"README", "CONFORMANCE", "ERRATA", "ERRATA.es"})

#: The documented topics, in the order the landing page lists them. Each is a
#: folder of `content/docs/` whose `index` page links the guides inside it, so
#: the grouping follows the content rather than a second hand-kept list.
AREAS: tuple[tuple[str, str], ...] = (
    ("signals", "Signal analysis"),
    ("fluids", "The medium"),
    ("solids", "Elastic solids"),
    ("io", "Files"),
    ("perception", "Hearing and perception"),
    ("buildings", "Rooms and buildings"),
    ("materials", "Materials and surfaces"),
    ("vibration", "Vibration and structure-borne sound"),
    ("environment", "Environment and transport"),
    ("aircraft", "Aircraft noise"),
    ("underwater", "Underwater acoustics"),
    ("devices", "Sources and devices"),
    ("simulation", "Wave simulation"),
)

#: Pages that open the documentation rather than belonging to a topic. About
#: joined them once it gained a mirror edition; before that it was linked by
#: absolute URL from the provenance section instead. It used to be listed
#: without a mirror and silently dropped, which is why an unresolvable entry is
#: fatal now.
START_ROUTES = (
    "start/getting-started",
    "start/environments",
    "start/environments/pip-and-uv",
    "start/environments/conda",
    "start/environments/jupyter",
    "start/environments/jupyterlite",
    "start/environments/docker",
    "start/environments/type-checking",
    "start/why-phonometry",
    "start/upgrading",
    "start/about",
    "start/support",
)

#: The start page that travels in a shard of its own (see :func:`_shard_plan`).
UPGRADING_ROUTE = "start/upgrading"

#: The kinds of page ``routes.json`` names (site/src/lib/page-markdown.mjs
#: ``pageKind``).
KINDS = frozenset({"home", "api", "catalogue", "errata-family", "guide"})

#: The header lines of a copy that carry a date read from git. ``make llms``
#: writes llms.txt from copies without them (``agent-md.mjs --dump
#: --undated``), so a shard is measured as if both were there, whether they are
#: or not: the cut, and the file names llms.txt lists, cannot then depend on
#: what git answered.
DATED_HEADER_KEYS = ("Published", "Updated")

#: What the dated lines take when they are there: the key, ``: ``, a
#: ``YYYY-MM-DD`` day and the end of the line.
DATED_LINES_BYTES = sum(len(f"{key}: 0000-00-00\n") for key in DATED_HEADER_KEYS)

#: A dated header line, as the header writes one.
_DATED_LINE = re.compile(
    rf"^(?:{'|'.join(DATED_HEADER_KEYS)}): [0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$"
)

#: What closes every page in a shard and in llms-full.txt: a blank line and a
#: rule. A page opens with the ``# `` title of its copy and the sentence under
#: it, which is how site/scripts/check-markdown-twins.mjs finds each page again.
PAGE_END = "\n\n---\n"


@dataclasses.dataclass(frozen=True)
class Page:
    """One English route, as ``routes.json`` describes it."""

    route: str
    kind: str
    title: str
    description: str
    standards: tuple[str, ...]
    #: The copy's path in the dump, or None for a page these files do not
    #: carry (the landing page, the API reference).
    copy: str | None


def _source_of(route: str) -> pathlib.Path:
    """The site page a route is built from, in either language."""
    for candidate in (
        *(CONTENT / f"{route}{ext}" for ext in (".md", ".mdx")),
        *(CONTENT / route / f"index{ext}" for ext in (".md", ".mdx")),
    ):
        if route and candidate.is_file():
            return candidate
    if not route and (CONTENT / "index.mdx").is_file():
        return CONTENT / "index.mdx"
    msg = f"generate_llms.py: no site page for the route {route!r}"
    raise SystemExit(msg)


#: The escapes of a YAML double-quoted scalar (YAML 1.2, section 5.7) that
#: stand for one character each; ``\x``, ``\u`` and ``\U`` take two, four and
#: eight hex digits.
_YAML_ESCAPES = {
    "0": "\0",
    "a": "\a",
    "b": "\b",
    "t": "\t",
    "\t": "\t",
    "n": "\n",
    "v": "\v",
    "f": "\f",
    "r": "\r",
    "e": "\x1b",
    " ": " ",
    '"': '"',
    "/": "/",
    "\\": "\\",
    "N": "\x85",
    "_": "\xa0",
    "L": "\u2028",
    "P": "\u2029",
}

_YAML_ESCAPE = re.compile(
    r"\\(?:x([0-9A-Fa-f]{2})|u([0-9A-Fa-f]{4})|U([0-9A-Fa-f]{8})|(.))", re.DOTALL
)


def _yaml_double_quoted(text: str, where: str) -> str:
    """The value of a YAML double-quoted scalar written on one line, its escapes read.

    The site reads its frontmatter with a YAML parser, so a page may write
    ``\u00e7`` for a ``ç``; an escape YAML does not have stops the run rather
    than reading as something the page does not say.
    """

    def escape(found: re.Match[str]) -> str:
        digits = found.group(1) or found.group(2) or found.group(3)
        if digits:
            return chr(int(digits, 16))
        if found.group(4) not in _YAML_ESCAPES:
            msg = f"generate_llms.py: {where} writes {found.group(0)!r}, which is no YAML escape"
            raise SystemExit(msg)
        return _YAML_ESCAPES[found.group(4)]

    return _YAML_ESCAPE.sub(escape, text)


def _frontmatter_field(path: pathlib.Path, name: str) -> str:
    """One scalar of a page's frontmatter, written on its own line, as YAML reads it.

    The site's pages write their title and description on one line each,
    double-quoted, single-quoted or bare, and the site reads them with a YAML
    parser: a double-quoted value's escapes are YAML's, a single-quoted one
    doubles its quotation mark, and a bare one ends before a comment. A value
    in any other shape (a block scalar, a flow collection, one that runs on to
    the next line) stops the run, as does a page without the field, since
    every line of the index that names a page says what it is about from it.
    ``tests/test_generate_llms.py`` holds this reader to a YAML parser on
    every page of the site.
    """
    text = path.read_text(encoding="utf-8")
    shown = _shown(path)
    head = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    found = head and re.search(
        rf"""^{name}:[ \t]*(?:"((?:[^"\\]|\\.)*)"|'((?:[^']|'')*)'|([^\s"'|>\[{{&*!%@`#][^\n]*?))(?:[ \t]+\#[^\n]*)?[ \t]*$""",
        head.group(1),
        re.MULTILINE,
    )
    if not found:
        msg = (
            f"generate_llms.py: {shown} has no frontmatter {name} written on one "
            "line, double-quoted, single-quoted or bare"
        )
        raise SystemExit(msg)
    double, single, bare = found.groups()
    if double is not None:
        return _yaml_double_quoted(double, f"{shown}, {name}")
    if single is not None:
        return single.replace("''", "'")
    return bare


def _description(route: str) -> str:
    """What a page is about, as its own meta description says."""
    return _frontmatter_field(_source_of(route), "description")


def _check_areas_cover_the_tree() -> None:
    """AREAS keeps the order and the labels; the tree decides membership.

    An unlisted topic folder used to vanish quietly: the page counter rose, the
    text landed in llms-full.txt, and the page was named nowhere in the index
    and carried by no shard, with exit 0. The docstring promised that drift
    could not happen quietly, and for this one list it could.
    """
    listed = {slug for slug, _ in AREAS}
    on_disk = {
        path.parent.name
        for path in CONTENT.glob("*/index.md*")
        if path.parent.name not in ("es", "start", "reference")
    }
    missing = sorted(on_disk - listed)
    ghosts = sorted(listed - on_disk)
    if missing or ghosts:
        parts = []
        if missing:
            parts.append("topic folder(s) with no AREAS entry: " + ", ".join(missing))
        if ghosts:
            parts.append("AREAS entr(ies) with no topic folder: " + ", ".join(ghosts))
        raise SystemExit("generate_llms.py: " + "; ".join(parts))


def _version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def _python_floor() -> str:
    """The oldest Python ``requires-python`` admits, as ``pyproject.toml`` says it."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        spec = tomllib.load(handle)["project"]["requires-python"]
    match = re.fullmatch(r">=\s*(\d+\.\d+)", spec.strip())
    if match is None:
        msg = f"generate_llms.py: requires-python {spec!r} is not a single floor"
        raise SystemExit(msg)
    return match.group(1)


def _conformance_counts() -> tuple[int, int, int, int]:
    """Checks, domains, normative designations and further published sources.

    Read from the conformance artefact. These integers used to be recovered by
    matching a regular expression against the report's headline sentence,
    which is how an English sentence became a wire format that three files
    parsed independently. They are fields now. The citation groups are not
    among them: they count citation strings, a book cited at seven clauses
    being seven of them, and the summary stated that figure as a count of
    standards.
    """
    source = DOCS / "conformance.json"
    try:
        counts = json.loads(source.read_text(encoding="utf-8"))["counts"]
        return (
            int(counts["checks"]),
            int(counts["domains"]),
            int(counts["designations"]),
            int(counts["sources"]),
        )
    except (OSError, ValueError, KeyError) as error:
        msg = (
            f"docs/conformance.json: cannot read the conformance counts "
            f"({error}). Regenerate it with `make conformance`."
        )
        raise SystemExit(msg) from error


#: What to run when the dump is missing or older than the site.
_REDUMP = (
    "Write it again with `make llms`, or with `node scripts/agent-md.mjs "
    "--dump ../build/agent-md --undated` from site/."
)


@functools.cache
def _read_dump(pages: pathlib.Path, _stamp: tuple[int, int] | None) -> dict[str, Page]:
    """Every English route of a dump, by route, as ``routes.json`` lists them.

    Read once per state of ``routes.json`` (*_stamp*, its modification time
    and size), so a dump written again is read again.
    """
    listing = pages / "routes.json"
    try:
        entries = json.loads(listing.read_text(encoding="utf-8"))["pages"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        msg = (
            f"generate_llms.py: cannot read the pages at {listing} ({error}). {_REDUMP}"
        )
        raise SystemExit(msg) from error
    found: dict[str, Page] = {}
    for entry in entries:
        page = Page(
            route=str(entry["route"]),
            kind=str(entry["kind"]),
            title=str(entry["title"]),
            description=str(entry["description"]),
            standards=tuple(str(item) for item in entry["standards"]),
            copy=None if entry["copy"] is None else str(entry["copy"]),
        )
        if page.kind not in KINDS:
            msg = f"generate_llms.py: {listing} gives {page.route!r} the unknown kind {page.kind!r}"
            raise SystemExit(msg)
        found[page.route] = page
    return found


def _dump() -> dict[str, Page]:
    """The routes of the dump this run reads (:data:`PAGES`)."""
    try:
        stat = (PAGES / "routes.json").stat()
    except OSError:
        return _read_dump(PAGES, None)
    return _read_dump(PAGES, (stat.st_mtime_ns, stat.st_size))


def _content_routes() -> set[str]:
    """Every English route of the site source, as the docs collection names them.

    A file's route is its path under ``src/content/docs`` without the
    extension, an ``index`` file standing for its folder and the root one for
    the landing page (site/src/lib/page-markdown.mjs ``routeOf``).
    """
    routes = set()
    for path in CONTENT.rglob("*.md*"):
        relative = path.relative_to(CONTENT).with_suffix("").as_posix()
        if relative.split("/")[0] == "es":
            continue
        routes.add(re.sub(r"(?:^|/)index$", "", relative))
    return routes


def _check_dump_matches_the_tree() -> None:
    """The dump has every English page of the site source, and no other.

    A dump is written by a separate command, so one left from an earlier
    checkout would otherwise publish an index of pages that have moved, with
    the new ones missing and no error anywhere.
    """
    dumped = set(_dump())
    on_disk = _content_routes()
    missing = sorted(on_disk - dumped)
    extra = sorted(dumped - on_disk)
    if missing or extra:
        parts = []
        if missing:
            parts.append(
                "page(s) of the site the dump does not hold: " + ", ".join(missing)
            )
        if extra:
            parts.append(
                "route(s) of the dump the site no longer has: " + ", ".join(extra)
            )
        msg = (
            f"generate_llms.py: the dump at {PAGES} is not the site's: "
            + "; ".join(parts)
            + f". {_REDUMP}"
        )
        raise SystemExit(msg)


def _routes() -> list[str]:
    """Every page whose whole text these files carry, by route, sorted."""
    return sorted(route for route, page in _dump().items() if page.copy is not None)


def _page(route: str) -> Page:
    """The dump's entry for a route, which must be there."""
    page = _dump().get(route)
    if page is None:
        msg = f"generate_llms.py: the dump at {PAGES} has no page {route!r}. {_REDUMP}"
        raise SystemExit(msg)
    return page


def _mirror_pages() -> list[str]:
    """Every page of the hand-written mirror under docs/, as its path there.

    The mirror is laid out like the site, so the route is the path: the page
    at ``docs/signals/filters/filter-banks.md`` mirrors
    ``/signals/filters/filter-banks/``. Raises if a mirror page has no page on
    the site, which would otherwise keep a page of the GitHub edition that the
    site no longer has.
    """
    pages: list[str] = []
    unmapped: list[str] = []
    for path in sorted(DOCS.rglob("*.md")):
        if path.parent == DOCS and path.stem in NOT_PAGES:
            continue
        # Files git ignores are somebody's local working notes, not the mirror:
        # they have no site page by design, and CI never sees them. Without
        # this the target cannot run at all in a checkout that has any.
        if _git_ignored(path):
            continue
        # The contributor guide is for the repository's readers (people and
        # coding agents working on phonometry), not the library's: it has no
        # site page and stays out of the mirror's checks by design.
        if path.relative_to(DOCS).parts[0] == "contributing":
            continue
        route = path.relative_to(DOCS).with_suffix("").as_posix()
        # A folder's own page is `<folder>/index.md`, as on the site.
        route = route.removesuffix("/index")
        published = any(
            (CONTENT / f"{route}{ext}").exists() for ext in (".md", ".mdx")
        ) or any((CONTENT / route / f"index{ext}").exists() for ext in (".md", ".mdx"))
        if not published:
            unmapped.append(route)
            continue
        pages.append(path.relative_to(DOCS).as_posix())
    if unmapped:
        raise SystemExit(
            "generate_llms.py: no site page for "
            + ", ".join(f"docs/{route}.md" for route in unmapped)
            + ". The mirror mirrors the site: move the file to the route its "
            "page has, or delete it if the page is gone."
        )
    return pages


def _api_routes() -> list[str]:
    """Every generated API reference page route, its index left out."""
    return sorted(
        route
        for route, page in _dump().items()
        if page.kind == "api" and route != "reference/api"
    )


def _guide_routes() -> set[str]:
    """Every guide route: the pages of a topic folder, overviews excluded."""
    topics = {slug for slug, _ in AREAS}
    return {
        path.relative_to(CONTENT).with_suffix("").as_posix()
        for topic in topics
        for path in (CONTENT / topic).rglob("*.md*")
        if path.stem != "index"
    }


def _overview(folder: pathlib.Path) -> pathlib.Path:
    """The overview page of a topic or subgroup folder, whatever it is called."""
    for name in ("index.md", "index.mdx"):
        if (folder / name).exists():
            return folder / name
    return folder / "index.md"


#: A link to a page of the site, in the source (``/phonometry/<route>/``) or in
#: a copy (``https://docs.jmrp.io/phonometry/<route>/``), capturing the route.
_SITE_LINK = re.compile(r"/phonometry/([a-z0-9-]+(?:/[a-z0-9-]+)*)/")


def _linked(text: str, candidates: Iterable[str]) -> list[str]:
    """The *candidates* a text links, in the order it first links them."""
    allowed = set(candidates)
    return [
        route for route in dict.fromkeys(_SITE_LINK.findall(text)) if route in allowed
    ]


def _linked_guides(overview: pathlib.Path, guides: set[str], folder: str) -> list[str]:
    """Guide routes an overview links, in order, restricted to its own folder.

    The prose gives the reading order, which is the point of reading it, but an
    overview also cross-references guides that live elsewhere. Membership is
    structural: a page belongs to the folder it is in, and only its own
    overview can order it.
    """
    text = overview.read_text(encoding="utf-8") if overview.exists() else ""
    return [
        route for route in _linked(text, guides) if route.rsplit("/", 1)[0] == folder
    ]


def _folder_order(folder: str, guides: set[str]) -> list[str]:
    """The guides of one folder, in the order its own overview teaches them."""
    ordered = _linked_guides(_overview(CONTENT / folder), guides, folder)
    ordered += [
        route
        for route in sorted(guides)
        if route.rsplit("/", 1)[0] == folder and route not in ordered
    ]
    return ordered


def _subgroups(topic: str) -> list[str]:
    """Subgroup folders of a topic, in the order the topic overview links them."""
    folders = sorted(
        path.parent.relative_to(CONTENT).as_posix()
        for path in (CONTENT / topic).rglob("index.md*")
        if path.parent != CONTENT / topic
    )
    text = _overview(CONTENT / topic).read_text(encoding="utf-8")
    mentioned = _linked(text, folders)
    return mentioned + [folder for folder in folders if folder not in mentioned]


def _area_members() -> dict[str, list[str]]:
    """Topic slug -> guide routes, in the order the overviews teach them.

    A page belongs to the folder it is in, which is the taxonomy the tree
    already states; the prose of each overview only decides the order, since
    that is what a reader is being led through. Anything an overview does not
    mention still appears, alphabetically, after what it does.
    """
    guides = _guide_routes()
    members: dict[str, list[str]] = {}
    claimed: set[str] = set()
    for slug, _label in AREAS:
        routes = _folder_order(slug, guides)
        for folder in _subgroups(slug):
            routes += _folder_order(folder, guides)
        found = [route for route in routes if route not in claimed]
        claimed.update(found)
        members[slug] = found
    leftover = sorted(guides - claimed)
    if leftover:
        members["other"] = leftover
    return members


#: Manual carve-outs from a folder's own shard, for a folder whose guides
#: answer different questions a reader would fetch apart. A shard that is only
#: too long for one fetch is cut into numbered parts by itself (see
#: :func:`_shard_parts`); a carve-out is a grouping the domain already makes,
#: so a reader fetching one shard gets a coherent set of guides and not an
#: arbitrary half, and it stays even where the parts would do.
#:
#: ``buildings/insulation`` has twelve guides, and its own overview groups them
#: by hand (``docs/buildings/insulation/index.md``: "Laboratory.", "Field.",
#: "Ratings and the envelope."). The ratings and the envelope carve out, and so
#: do the four laboratory guides, the ISO 10140 measurement with the
#: application rules of ISO 10140-1 and the two laboratory methods beside it,
#: which leaves the field measurements in the folder's own shard.
#:
#: ``devices/emission`` has thirteen, and the family sorts its determination
#: routes by the quantity actually measured: sound pressure, sound intensity,
#: and the surface velocity of the casing. The intensity pair carves out, and
#: so do the four pressure routes that read a reverberant field instead of an
#: enveloping surface: the reverberation room of ISO 3741, the small test
#: rooms of ISO 3743, the in situ comparison of ISO 3747 and the 16 kHz octave
#: of ISO 9295, which extends the first above 10 kHz. The pressure routes that
#: read an enveloping surface carve out as well: ISO 3744, ISO 3746 and
#: ISO 3745, the ISO 26101 qualification of the free-field room the last one
#: needs with the ISO 6926 reference source, and the IEC 61063 test code that
#: takes the survey surface of ISO 3746 to a steam turbine set in its hall.
#: That leaves the choice of route, the in-duct method, the surface vibration
#: route and the work station in the folder's own shard.
#:
#: ``buildings/rooms`` has eleven, and four of them are the auditorium
#: measures of the ISO 3382-1 annexes and the tables that report them, which
#: the standard itself keeps apart from the decay analysis of its normative
#: body. Those four carve out.
#:
#: ``devices/noise-control`` has nine, and it divides twice. Two of them are
#: throttling-valve noise: a different source, a different standard family
#: (IEC 60534-8) and a different reader from the fan-to-room duct chain and the
#: elements it calls. Three more measure a device that was already built rather
#: than predicting one that is being designed, which is the division the
#: standards themselves make: a catalogue figure comes from a laboratory
#: substitution, an acceptance figure comes from the installation. A folder may
#: therefore carry several splits, and each is a grouping the domain already
#: makes rather than a cut chosen to fit the budget.
#:
#: ``signals/metrology`` has nine, and its own overview climbs a chain: the
#: instruments a laboratory grades, then "one step up the chain, to the
#: microphone itself", the comparison of IEC 61094-5 and IEC 61094-8, and "the
#: top of that chain", the reciprocity of IEC 61094-2 and IEC 61094-3. The two
#: microphone calibrations of the IEC 61094 series carve out, which leaves the
#: calibration of a recording, the uncertainty, the data qualification and the
#: verdicts on meters and their corrections in the folder's own shard.
#:
#: In all of them, the leaf names are guide filenames and the label mirrors the
#: heading. The carved-out shard has no page of its own, so its Overview link
#: still resolves to the parent folder (see _shard_folders and _shard_label
#: below).
MANUAL_SPLITS: dict[str, tuple[tuple[str, str, tuple[str, ...]], ...]] = {
    "buildings/insulation": (
        (
            "buildings-insulation-laboratory",
            "Laboratory insulation measurement",
            (
                "insulation-lab",
                "lab-application-rules",
                "insulation-intensity",
                "flanking-lab",
            ),
        ),
        (
            "buildings-insulation-ratings",
            "Insulation ratings and the envelope",
            ("insulation-ratings", "facade-insulation", "spanish-building-code"),
        ),
    ),
    "devices/emission": (
        (
            "devices-emission-intensity",
            "Sound intensity and sound power from it",
            ("intensity", "sound-power-intensity"),
        ),
        (
            "devices-emission-reverberant",
            "Sound power in a reverberant field",
            (
                "sound-power-reverberation",
                "sound-power-test-rooms",
                "sound-power-in-situ",
                "sound-power-high-frequency",
            ),
        ),
        (
            "devices-emission-enveloping",
            "Sound power on an enveloping surface",
            (
                "sound-power-pressure",
                "free-field-qualification",
                "sound-power-turbines",
            ),
        ),
    ),
    "devices/noise-control": (
        (
            "devices-noise-control-valves",
            "Control valve noise (IEC 60534-8)",
            ("control-valve-noise", "valve-cavitation"),
        ),
        (
            "devices-noise-control-measured",
            "Measuring a device that is already built",
            (
                "silencer-measurement",
                "enclosure-cabin-insulation",
                "in-situ-noise-control",
            ),
        ),
    ),
    "signals/metrology": (
        (
            "signals-metrology-microphones",
            "Microphone calibration (IEC 61094)",
            ("comparison-calibration", "reciprocity-calibration"),
        ),
    ),
    "buildings/rooms": (
        (
            "buildings-rooms-auditorium",
            "Auditorium measures of the ISO 3382-1 annexes",
            (
                "sound-strength",
                "spatial-impression",
                "stage-and-uncertainty",
                "reporting-and-qualification",
            ),
        ),
    ),
}


@functools.cache
def _shard_folders() -> dict[str, str]:
    """Shard slug -> the content folder it names.

    Undoing ``folder.replace("/", "-")`` with one string replace was lossy for
    a folder nested two levels down: ``devices-emission-vehicles`` mapped back
    to ``devices/emission-vehicles``, whose overview does not exist, and every
    consequence was silent. The mapping is recorded at the same walk that
    creates the slugs, never reconstructed from the slug.
    """
    folders = {topic: topic for topic, _ in AREAS}
    for topic, _ in AREAS:
        for path in (CONTENT / topic).rglob("index.md*"):
            if path.parent != CONTENT / topic:
                folder = path.parent.relative_to(CONTENT).as_posix()
                folders[folder.replace("/", "-")] = folder
    for folder, splits in MANUAL_SPLITS.items():
        for slug, _label, _leaves in splits:
            folders[slug] = folder
    return folders


@functools.cache
def _shard_members() -> dict[str, list[str]]:
    """Shard slug -> guide routes, at the finest grouping the tree offers.

    The index groups by the topics a reader recognises, but several of
    those are large enough that a whole-topic shard blows the fetch budget on
    its own. Most topics are already subdivided in the tree (octave filtering,
    levels and weighting, and so on), each subgroup with its own overview page,
    so sharding follows those subdivisions where they exist and falls back to
    the topic where they do not. The shard slug is the folder path with slashes
    turned into dashes, so ``signal/filters`` publishes as
    ``llms-signal-filters.txt``.
    """
    guides = _guide_routes()
    shards: dict[str, list[str]] = {}
    claimed: set[str] = set()

    def slug_of(folder: str) -> str:
        return folder.replace("/", "-")

    # Subgroups first: they are the finer grain, and claiming there keeps the
    # parent topic shard down to whatever it holds directly.
    subgroups = sorted(
        path.parent.relative_to(CONTENT).as_posix()
        for topic, _ in AREAS
        for path in (CONTENT / topic).rglob("index.md*")
        if path.parent != CONTENT / topic
    )
    for folder in subgroups:
        found = [
            route
            for route in _linked_guides(_overview(CONTENT / folder), guides, folder)
            if route not in claimed
        ]
        found += [
            route
            for route in sorted(guides)
            if route.rsplit("/", 1)[0] == folder
            and route not in claimed
            and route not in found
        ]
        if not found:
            continue
        claimed.update(found)
        for split_slug, _label, leaves in MANUAL_SPLITS.get(folder, ()):
            split_routes = {f"{folder}/{leaf}" for leaf in leaves}
            missing = sorted(split_routes - set(found))
            if missing:
                raise SystemExit(
                    f"generate_llms.py: MANUAL_SPLITS for {folder} names "
                    "route(s) not among its guides: " + ", ".join(missing)
                )
            # Order follows found (the overview's own reading order), not the
            # tuple above: MANUAL_SPLITS just names which guides move, not the
            # order to read them in.
            shards[split_slug] = [route for route in found if route in split_routes]
            found = [route for route in found if route not in split_routes]
        shards[slug_of(folder)] = found
    for topic, _label in AREAS:
        found = [
            route
            for route in sorted(guides)
            if route.split("/")[0] == topic and route not in claimed
        ]
        # Unconditional: a topic whose guides are all claimed by its subgroups
        # still gets a shard, carrying its own overview. Without it, the five
        # fully subdivided topics had their overview text in no shard at all.
        claimed.update(found)
        shards[slug_of(topic)] = found
    leftover = sorted(guides - claimed)
    if leftover:
        shards["other"] = leftover
    return shards


def _page_title(route: str) -> str:
    """A page's title, as its frontmatter gives it and its tab shows it."""
    return _page(route).title


def _shard_label(slug: str) -> str:
    """The human name of a shard: the title of the overview it opens with.

    ``slug.capitalize()`` named none of the sections the site shows: it said
    "Signal metrology" where the site says "Calibration and uncertainty" and
    "Buildings rooms" where it says "Room acoustics". The overview's own title
    is the name a reader of the site recognises.
    """
    labels = dict(AREAS)
    if slug in labels:
        return labels[slug]
    split_labels = {
        split_slug: label
        for splits in MANUAL_SPLITS.values()
        for split_slug, label, _leaves in splits
    }
    if slug in split_labels:
        return split_labels[slug]
    folder = _shard_folders().get(slug, slug)
    if folder in _dump():
        return _page_title(folder)
    return slug.replace("-", " ").capitalize()


#: A PEP 440 version, with the two segments that make it a pre-release named:
#: an alpha, beta or release candidate in any spelling PEP 440 normalises, and
#: a development release. The same reading as ``isPreRelease`` of
#: ``site/src/lib/pep440.mjs`` and packaging's ``Version.is_prerelease``;
#: ``site/src/data/pep440-pre-releases.json`` is the table all three are
#: tested on.
_PEP440 = re.compile(
    r"^v?\d+(?:\.\d+)*(?P<pre>[-_.]?(?:a|b|c|rc|alpha|beta|pre|preview)[-_.]?\d*)?"
    r"(?:-\d+|[-_.]?(?:post|rev|r)[-_.]?\d*)?(?P<dev>[-_.]?dev[-_.]?\d*)?"
    r"(?:\+[a-z0-9]+(?:[-_.][a-z0-9]+)*)?$",
    re.IGNORECASE,
)


def _is_pre_release(version: str) -> bool:
    """Whether *version* is a pre-release by PEP 440, which pip installs only when asked."""
    parsed = _PEP440.match(version.strip())
    if parsed is None:
        msg = f"generate_llms.py: VERSION {version!r} is not a PEP 440 version"
        raise SystemExit(msg)
    return parsed.group("pre") is not None or parsed.group("dev") is not None


def _pre_release_lines(version: str) -> list[str]:
    """The paragraph that says a pre-release is not on PyPI yet, or nothing.

    The install lines below install the last release PyPI has, so while
    VERSION is a pre-release the index says the version it documents is not
    there yet. It names no version PyPI serves, so it cannot go stale, and it
    goes by itself at the stamp.
    """
    if not _is_pre_release(version):
        return []
    return [f"phonometry {version} is a pre-release and is not on PyPI yet.", ""]


def _summary(version: str) -> list[str]:
    """The header every artifact opens with."""
    checks, domains, designations, sources = _conformance_counts()
    return [
        "# phonometry",
        "",
        (
            "> Acoustic measurement, analysis and prediction in Python. Sound level "
            "metrology, psychoacoustics, room and building acoustics, materials, "
            "vibration, environmental and transport noise, underwater acoustics, "
            "electroacoustics and wave simulation, with every metric implemented "
            f"from the text of its governing standard and {checks} numerical "
            "conformance checks enforced in CI, against "
            f"{designations} normative designations and {sources} further "
            "published sources."
        ),
        "",
        (
            f"phonometry v{version} is a pure-Python library built on NumPy/SciPy "
            f"(Python >= {_python_floor()}). Each result is a typed, frozen dataclass "
            "that carries the inputs it was computed from, draws its own figure with "
            "a one-line `.plot()` in English or Spanish, and, where a standard "
            "defines a reporting format, renders that format as a PDF with "
            "`.report()`. The "
            f"conformance report pins each of the {checks} checks to a standard, a "
            "clause or table, the normative expected value and the value the library "
            f"computes, across {domains} domains."
        ),
        "",
        (
            "The project was published as **PyOctaveBand** until version 3.0.0. "
            "Third-party references and dependency pins still using that name refer "
            "to this library."
        ),
        "",
        *_pre_release_lines(version),
        "Install:",
        "",
        "```bash",
        "pip install phonometry              # core (NumPy + SciPy only)",
        'pip install "phonometry[plot]"      # + matplotlib figures and .plot()',
        'pip install "phonometry[perf]"      # + numba-jitted impulse kernel',
        'pip install "phonometry[report]"    # + reportlab and svglib, for .report() PDF fiches',
        'pip install "phonometry[audio]"     # + python-soundfile, for FLAC, AIFF, Ogg/Opus, MP3 and compressed WAV',
        'pip install "phonometry[full]"      # all of the above (recommended)',
        'pip install "phonometry[torch]"     # + torch and array-api-compat, the FDTD engines on PyTorch; not in [full]',
        "```",
        "",
        (
            'I recommend `pip install "phonometry[full]"`, which enables every '
            "feature except the torch backend of the FDTD engines, which "
            "`[torch]` adds. On 32-bit Windows and 32-bit Linux, where numba, "
            "and so `[full]`, is not supported, "
            '`pip install "phonometry[plot,report,audio]"` installs the other '
            "three extras. The base install computes every metric on NumPy and "
            "SciPy alone; without the extras only the `.plot()` figures, the "
            "`.report()` PDF fiches (whose figure panel needs matplotlib as well "
            "as reportlab and svglib), the compressed audio formats and the "
            "torch backend of the FDTD engines are unavailable. The `impulse` "
            "time weighting still works without numba, on a pure-Python kernel "
            "that is only slower, and the FDTD engines run on NumPy either way, "
            "and on an NVIDIA GPU once CuPy is installed. `[full]` leaves torch "
            "out because the torch wheels PyPI serves on Linux bring gigabytes "
            "of CUDA libraries; on a Linux machine without an NVIDIA GPU, "
            "running `pip install torch --index-url "
            "https://download.pytorch.org/whl/cpu` before "
            '`pip install "phonometry[torch]"` takes the CPU wheels instead.'
        ),
        "",
        (
            "One caveat about `[full]`: numba is the only extra that caps "
            "NumPy, and it raises that cap only once it supports a new NumPy "
            "minor, so in the weeks after a NumPy minor release "
            "`phonometry[full]` (like `phonometry[perf]`) can resolve one minor "
            "behind what a plain install gets. numba only makes the `impulse` "
            "time weighting faster, so install `phonometry[plot,report]` "
            "instead if you need the newest NumPy the day it ships."
        ),
        "",
        (
            "Minimal usage (all functions treat time as the LAST axis; 2D input is "
            "(channels, samples)):"
        ),
        "",
        "```python",
        "import numpy as np",
        "from phonometry import filters, signals",
        "",
        "fs = 48000",
        "x = np.random.randn(fs)              # 1 s of signal (pressure units)",
        "bands = filters.octave_filter(x, fs, fraction=3)         # 1/3-octave bands",
        "spl, freq = bands.levels, bands.frequencies",
        "la = signals.laeq(x, fs)                                 # A-weighted Leq",
        "stats = signals.ln_levels(x, fs, n=(10, 50, 90))         # statistical levels",
        "```",
        "",
        (
            "If you are an AI assistant setting this up for a user: install from PyPI "
            "(no system dependencies on Linux with glibc on x86-64 or ARM64, on "
            "macOS on ARM or on 64-bit Windows; Getting Started says what other "
            "platforms build from source), remember integer audio (e.g. wavfile.read "
            "int16) is handled automatically, use `calibration_factor` from "
            "`sensitivity()` for real dB SPL, and prefer `OctaveFilterBank` over "
            "repeated `octave_filter()` calls in tight loops (although designs are "
            "cached either way). The library computes standardized quantities; it is "
            "not a certified instrument and does not acquire data from hardware."
        ),
        "",
    ]


def _shard_url(name: str) -> str:
    """Where a shard file is published, *name* being what ``llms-`` precedes."""
    return f"{SITE_URL}/llms/llms-{name}.txt"


def _part_names(slug: str, count: int) -> tuple[str, ...]:
    """The file names a shard publishes under: its own, or one per part.

    A shard in one piece keeps its slug. One cut into parts numbers them from
    1, extending the slug the way a carved-out shard extends the name of the
    folder it came from: ``llms-upgrading.txt`` becomes
    ``llms-upgrading-1.txt``, ``llms-upgrading-2.txt`` and so on.
    """
    if count == 1:
        return (slug,)
    return tuple(f"{slug}-{number}" for number in range(1, count + 1))


def _part_label(label: str, number: int, count: int) -> str:
    """The name of one part of a shard, in its own head and in the index."""
    return f"{label}, part {number} of {count}"


def _full_text_entries(label: str, files: tuple[str, ...]) -> list[str]:
    """The index lines for one shard: one, or one per part, in order."""
    if len(files) == 1:
        return [f"- [{label}]({_shard_url(files[0])})"]
    return [
        f"- [{_part_label(label, number, len(files))}]({_shard_url(name)})"
        for number, name in enumerate(files, start=1)
    ]


def _full_text_links(files: tuple[str, ...]) -> str:
    """The full-text links a carved-out heading of the index carries."""
    if len(files) == 1:
        return f"[full text]({_shard_url(files[0])})"
    return " · ".join(
        f"[{_part_label('full text', number, len(files))}]({_shard_url(name)})"
        for number, name in enumerate(files, start=1)
    )


def _shard_urls(shard_files: Mapping[str, tuple[str, ...]], slug: str) -> str:
    """Every URL of one shard, comma separated, for a sentence of the index."""
    return ", ".join(_shard_url(name) for name in shard_files.get(slug, (slug,)))


def _site_entry(label: str, route: str) -> str:
    """The index line of a site page: its label linked, then what it is about.

    The line says what the page is about with the page's own meta
    description, so that a reader of the index can choose a page without
    fetching it.
    """
    return f"- [{label}]({SITE_URL}/{route}/): {_description(route)}"


def _page_entry(route: str) -> str:
    """The index line of one page: its title linked, then what it is about."""
    return _site_entry(_page_title(route), route)


def _start_section() -> list[str]:
    # The section's own page and the task index have no mirror page, so they
    # are listed by their site title, as the guides index is.
    tasks = "start/tasks"
    lines = [
        "## Start here",
        "",
        _site_entry("Overview", "start"),
        _site_entry(_frontmatter_field(_source_of(tasks), "title"), tasks),
    ]
    for route in START_ROUTES:
        if route not in _dump():
            # These are listed by hand, so an unresolvable one is always a
            # bug; the About page went missing this way once, silently.
            msg = (
                f"generate_llms.py: START_ROUTES names {route}, "
                "which is not a page of the site"
            )
            raise SystemExit(msg)
        lines.append(_page_entry(route))
    return [
        *lines,
        _site_entry("Guides index", "start/guides"),
        _site_entry("Glossary of quantities", "reference/glossary"),
        "",
    ]


def _area_section(
    slug: str, routes: list[str], shard_files: Mapping[str, tuple[str, ...]]
) -> list[str]:
    """One topic of the index: its overview, then its guides, run by shard."""
    lines = [f"## {dict(AREAS).get(slug, 'Other guides')}", ""]
    if slug != "other":
        lines.append(_site_entry("Overview", slug))
    shard_of = {
        route: shard for shard, members in _shard_members().items() for route in members
    }
    # The shards are per subgroup, so the index says which subgroup, and
    # therefore which shard, each run of guides belongs to: a client that
    # wants the full text of one part should not have to infer the shard
    # from the URL path.
    #
    # The runs are emitted shard by shard rather than in the folder's own
    # reading order, because a heading claims everything under it until the
    # next one. Walking the reading order and switching heading on first
    # sight of a new shard put a guide of the parent shard under a carved
    # out heading whenever the carve-out was not the tail of that order,
    # which is how the surface-velocity route came to sit under a heading
    # about sound intensity. Within each run the reading order is kept.
    grouped: dict[str, list[str]] = {}
    for route in routes:
        grouped.setdefault(shard_of.get(route, slug), []).append(route)
    for group in [slug, *(g for g in grouped if g != slug)]:
        if group != slug and group in grouped:
            folder = _shard_folders().get(group, group)
            lines += [
                "",
                f"### {_shard_label(group)}",
                "",
                (
                    f"{_site_entry('Overview', folder)} · "
                    + _full_text_links(shard_files.get(group, (group,)))
                ),
            ]
        lines += [_page_entry(route) for route in grouped.get(group, [])]
    lines.append("")
    return lines


def _is_reference_page(route: str) -> bool:
    """A page of the reference section the index lists one by one.

    The API reference is listed by its index alone (each module is in
    Optional), and the errata families and the catalogues travel in shards of
    their own, which the Full text section lists.
    """
    page = _dump()[route]
    if route == "reference/api":
        return True
    return page.kind == "guide" and (
        route == "reference" or route.startswith("reference/")
    )


def _reference_section(shard_files: Mapping[str, tuple[str, ...]]) -> list[str]:
    lines = [
        "## Theory and reference",
        "",
        (
            "The theory pages travel in their own shard "
            f"({_shard_urls(shard_files, 'theory')}), the glossary in another "
            f"({_shard_urls(shard_files, 'glossary')}), and the rest of the "
            f"reference in {_shard_urls(shard_files, 'reference')}. The "
            "conformance report, the errata register and every published "
            "catalogue have shards of their own, which the Full text section "
            "below lists."
        ),
        "",
        _site_entry("Overview", "reference"),
    ]
    lines += [
        _page_entry(route) for route in sorted(filter(_is_reference_page, _dump()))
    ]
    lines.append("")
    return lines


def _provenance_section() -> list[str]:
    return [
        "## Evidence and provenance",
        "",
        (
            f"- [Conformance report]({SITE_URL}/reference/conformance/): every check, "
            "with the standard, the clause, the normative expected value, the value "
            "the library computes and the delta"
        ),
        (
            f"- [Errata in published sources]({SITE_URL}/reference/errata/): defects "
            "found in published standards, each re-derived from that standard's own "
            "normative clauses"
        ),
        (
            f"- [Published catalogues]({SITE_URL}/reference/catalogues/): every "
            "value this library read off a printed page, with the book, the "
            "table and the page it came from, and what the page printed where "
            "a number is missing"
        ),
        (
            f"- [Report fiches]({SITE_URL}/reference/reports/): every PDF fiche "
            "the library renders, in the reporting format its standard defines, "
            "with the guide that explains the measurement behind each one"
        ),
        f"- [Bibliography]({SITE_URL}/reference/bibliography/)",
        f"- [About the author and the method]({SITE_URL}/start/about/)",
        "",
        "## Source and metadata",
        "",
        f"- [Repository]({REPO_URL})",
        "- [PyPI](https://pypi.org/project/phonometry/)",
        f"- [Changelog]({REPO_URL}/blob/main/CHANGELOG.md)",
        f"- [Cite this software]({REPO_URL}/blob/main/CITATION.cff)",
        f"- [Archived release (DOI)](https://doi.org/{DOI})",
        "- [Licence: MIT](https://opensource.org/license/MIT)",
        "",
    ]


def _count(number: int, noun: str) -> str:
    """``1 entry``, ``2 entries``, ``260 rows``."""
    if number == 1:
        return f"1 {noun}"
    return f"{number} {noun[:-1]}ies" if noun.endswith("y") else f"{number} {noun}s"


def _errata_families() -> list[FamilyPage]:
    """The pages of the errata register, read from the register itself.

    :func:`generate_site_reports.family_pages` is what writes the site's
    family pages from ``docs/ERRATA.md``: it files each entry under its
    document family and knows the page of properties that are not errata
    apart, so an entry is counted where the register files it, not by the
    headings a page happens to carry.
    """
    return family_pages()


def _errata_section() -> list[str]:
    """One line per family page of the errata register, with its entry count.

    The page of the register's properties that are not errata is no family
    and has no entries: it is listed in a section of its own with what it is
    about, as the register's index lists it under a heading of its own.
    """
    families = sorted(_errata_families(), key=lambda page: page.family.slug)
    lines = [
        "## Errata by source",
        "",
        (
            "The errata register has one page per document family, each with "
            "the defects found in that family's printed text, the evidence and "
            f"what the library does about each (index: {SITE_URL}/{ERRATA_ROUTE}/)."
        ),
        "",
    ]
    apart: list[str] = []
    for page in families:
        route = f"{ERRATA_ROUTE}/{page.family.slug}"
        title = _frontmatter_field(_source_of(route), "title")
        if page.family.group == "not-errata":
            apart.append(_site_entry(title, route))
            continue
        lines.append(
            f"- [{title}]({SITE_URL}/{route}/): {_count(len(page.positions), 'entry')}"
        )
    lines.append("")
    if apart:
        lines += ["## Properties that are not errata", "", *apart, ""]
    return lines


@functools.cache
def _catalogue_rows() -> dict[str, int]:
    """The rows of each published catalogue, read from the data its pages table.

    The file is a JavaScript module that exports one object literal written as
    JSON (``scripts/generate_catalogue_data.py``), so its body after the export
    parses as JSON; a module of any other shape stops the run.
    """
    text = CATALOGUE_DATA.read_text(encoding="utf-8")
    found = re.search(
        r"^export const catalogues = (\{.*\});\s*\Z", text, re.DOTALL | re.MULTILINE
    )
    if found is None:
        msg = (
            f"generate_llms.py: {_shown(CATALOGUE_DATA)} is not the "
            "`export const catalogues = {...};` module generate_catalogue_data.py writes"
        )
        raise SystemExit(msg)
    data = json.loads(found.group(1))
    return {name: len(catalogue["rows"]) for name, catalogue in data.items()}


def _catalogue_section() -> list[str]:
    """One line per published catalogue page, with the rows it tables."""
    rows = _catalogue_rows()
    pages = sorted(
        path
        for path in (CONTENT / "reference" / "catalogues").glob("*.md*")
        if path.stem != "index"
    )
    # What the catalogues hold is said by their index page, in its own words.
    index = "reference/catalogues"
    lines = [
        "## Published catalogues",
        "",
        (
            f"{_description(index)} One page per catalogue, each listed here with "
            f"the rows it tables (index: {SITE_URL}/{index}/)."
        ),
        "",
    ]
    for path in pages:
        route = path.relative_to(CONTENT).with_suffix("").as_posix()
        shown = page_markup(path.read_text(encoding="utf-8"), kind="mdx")
        names = re.findall(r'<Catalogues\b[^>]*\bcatalogue="([^"]+)"', shown)
        unknown = [name for name in names if name not in rows]
        if not names or unknown:
            msg = (
                f"generate_llms.py: {_shown(path)} tables "
                f"{unknown or 'no catalogue'} of {_shown(CATALOGUE_DATA)}"
            )
            raise SystemExit(msg)
        title = _frontmatter_field(path, "title")
        count = _count(sum(rows[name] for name in names), "row")
        lines.append(
            f"- [{title}]({SITE_URL}/{route}/) ({count}): {_description(route)}"
        )
    lines.append("")
    return lines


def _joined(items: list[str]) -> str:
    """``a``, ``a and b``, ``a, b and c``."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _spanish_routes() -> set[str]:
    """Every route of the Spanish tree of the site source, without its ``es/``.

    The pages the site translates: an English route with none here is served
    under ``/es/`` as the English page (Starlight's fallback), which has no file
    of its own and so no copy (``routeOf`` of ``site/src/lib/page-markdown.mjs``).
    """
    routes = set()
    for path in (CONTENT / "es").rglob("*.md*"):
        relative = path.relative_to(CONTENT / "es").with_suffix("").as_posix()
        routes.add(re.sub(r"(?:^|/)index$", "", relative))
    return routes


#: The route the generated API reference lives under, named as one in the
#: sentence on the copies.
API_ROUTE = "reference/api"


def _copies_sentence() -> str:
    """Where a page's Markdown copy is, and which pages are in English only.

    Every page publishes a copy written from its own source
    (``site/scripts/agent-md.mjs --public``), the landing pages and the pages
    that show their data through a component included, so the sentence names
    no page without one. It names the pages the Spanish tree does not
    translate, whose Spanish address shows the English page.
    """
    sentence = (
        "Every page listed here has a Markdown copy beside it at "
        f"`<page>/index.md`, for example {SITE_URL}/start/getting-started/index.md, "
        "and its Spanish twin under `/es/` has one too where the page is translated."
    )
    english_only = sorted(_content_routes() - _spanish_routes())
    api = [r for r in english_only if r == API_ROUTE or r.startswith(f"{API_ROUTE}/")]
    untranslated = (
        [f"the {_count(len(api), 'page')} of the API reference"] if api else []
    )
    untranslated += [
        f'the "{_frontmatter_field(_source_of(r), "title")}" page'
        for r in english_only
        if r not in api
    ]
    if untranslated:
        listed = _joined(untranslated)
        verb = "are" if len(untranslated) > 1 or len(api) > 1 else "is"
        sentence += (
            f" {listed[0].upper()}{listed[1:]} {verb} in English only: at the "
            "Spanish address the site shows the English page, which points to "
            "its English copy."
        )
    return sentence


def _topic_shards(shard_slugs: Iterable[str]) -> list[str]:
    """The shards of the topics, in the order the site lists them.

    Grouped by topic, the topic's own shard first, so the list reads like the
    navigation rather than like a sort key. Within a topic the subgroups come
    in the order the topic overview teaches them, matching the navigation;
    alphabetical-by-slug put Calibration before Spectra in a topic whose
    overview teaches them the other way round. The slugs are the shards
    actually built this run: a hand-kept list here published a link to a shard
    that a content move could stop producing.
    """
    slugs = tuple(shard_slugs)
    folders = _shard_folders()
    ordered: list[str] = []
    for topic, _label in AREAS:
        nav_order = {folder: rank for rank, folder in enumerate(_subgroups(topic))}
        ordered += [slug for slug in slugs if slug == topic]
        ordered += sorted(
            (slug for slug in slugs if slug.startswith(f"{topic}-")),
            key=lambda slug: (
                nav_order.get(folders.get(slug, ""), len(nav_order)),
                slug,
            ),
        )
    return ordered


def _full_text_section(
    plan: Sequence[tuple[str, str, list[str]]],
    shard_files: Mapping[str, tuple[str, ...]],
) -> list[str]:
    intro = "One file per area, each small enough to fetch whole."
    if any(len(files) > 1 for files in shard_files.values()):
        intro += (
            " An area too long for one fetch travels in numbered parts, cut "
            "between its pages, and a page too long for one at its own sections."
        )
    intro += (
        " `llms-full.txt` is the complete concatenation and is far too large "
        "for a single fetch in most clients."
    )
    lines = ["## Full text", "", intro, ""]
    for slug, label, _routes in plan:
        lines += _full_text_entries(label, shard_files.get(slug, (slug,)))
    lines += [f"- [Everything]({SITE_URL}/llms-full.txt)", ""]
    return lines


def _closing_sections() -> list[str]:
    lines = [
        "## Spanish",
        "",
        (
            "Every page above also exists in Spanish under the `/es/` prefix, for "
            f"example {SITE_URL}/es/start/getting-started/. The two trees are kept at "
            "parity by a build check."
        ),
        "",
        "## Markdown copies",
        "",
        _copies_sentence(),
        "",
        "## Optional",
        "",
        (
            "The generated API reference, one page per module. Fetch these only when "
            "a specific signature is needed; the guides above explain the same "
            "functions in context."
        ),
        "",
        f"- [API reference index]({SITE_URL}/reference/api/)",
        # The curated table of every public name is a file of docs/ written by
        # hand, no page of the site, so llms-full.txt, which carries the
        # site's pages, leaves it out; its one line per name is linked here.
        (
            f"- [Quick API table on GitHub]({REPO_URL}/blob/main/{QUICK_API_TABLE}): "
            "every public name with one line on what it is, by subpackage"
        ),
    ]
    lines += [
        f"- [{route.removeprefix('reference/api/')}]({SITE_URL}/{route}/)"
        for route in _api_routes()
    ]
    lines.append("")
    return lines


def build_llms_txt(
    version: str,
    shard_files: Mapping[str, tuple[str, ...]],
    plan: Sequence[tuple[str, str, list[str]]] | None = None,
) -> str:
    """The index, *shard_files* naming the files each shard published.

    A shard in one piece names one file; a shard cut into parts names one per
    part (see :func:`_part_names`), and the index lists every one of them.
    """
    lines = _summary(version)
    lines += _start_section()
    for slug, routes in _area_members().items():
        lines += _area_section(slug, routes, shard_files)
    lines += _reference_section(shard_files)
    lines += _provenance_section()
    lines += _errata_section()
    lines += _catalogue_section()
    lines += _full_text_section(_shard_plan() if plan is None else plan, shard_files)
    lines += _closing_sections()
    return "\n".join(lines)


@dataclasses.dataclass(frozen=True)
class Copy:
    """A page's Markdown copy, as the llms files carry it.

    *head* runs from the ``# `` title through the rule that closes the header;
    *rest* is everything after it (the body and the References section), and
    the page as a shard holds it is ``head`` and ``rest`` a blank line apart.
    """

    route: str
    head: str
    rest: str

    @property
    def text(self) -> str:
        """The page as a shard and llms-full.txt hold it whole."""
        return f"{self.head}\n\n{self.rest}" if self.rest else self.head


def _split_copy(route: str, text: str) -> Copy:
    """A copy's head and rest, refusing a text that is not a copy.

    A copy opens with its ``# `` title, a blank line, the sentence that says
    what it is (``> ``), and the header's ``Key: value`` lines, closed by a
    ``---`` rule; a blank line separates that from the body.
    """
    lines = text.removesuffix("\n").split("\n")
    shaped = (
        len(lines) >= 4
        and lines[0].startswith("# ")
        and lines[1] == ""
        and lines[2].startswith("> ")
        and "---" in lines[3:]
    )
    if not shaped:
        msg = (
            f"generate_llms.py: the dump's copy of {route} does not open as a "
            f"Markdown copy (a title, the sentence under it and a header). {_REDUMP}"
        )
        raise SystemExit(msg)
    close = lines.index("---", 3)
    rest = lines[close + 1 :]
    if rest and rest[0] == "":
        rest = rest[1:]
    return Copy(route=route, head="\n".join(lines[: close + 1]), rest="\n".join(rest))


def _copy(route: str) -> Copy:
    """The copy of a page these files carry, from the dump."""
    page = _page(route)
    if page.copy is None:
        msg = f"generate_llms.py: the dump holds no copy of {route}, which is a {page.kind} page"
        raise SystemExit(msg)
    try:
        text = (PAGES / page.copy).read_text(encoding="utf-8")
    except OSError as error:
        msg = f"generate_llms.py: cannot read the copy of {route} ({error}). {_REDUMP}"
        raise SystemExit(msg) from error
    return _split_copy(route, text)


def _measured_head(head: str) -> int:
    """What a page's head takes in a shard, dated or not (:data:`DATED_LINES_BYTES`)."""
    undated = [line for line in head.split("\n") if not _DATED_LINE.match(line)]
    return len("\n".join(undated).encode("utf-8")) + DATED_LINES_BYTES


def _lines_bytes(lines: Iterable[str]) -> int:
    """What lines take joined, each counted with the newline after it."""
    return sum(len(line.encode("utf-8")) + 1 for line in lines)


@dataclasses.dataclass(frozen=True)
class _Unit:
    """A run of a page's lines that a part of a shard holds whole.

    A page is one unit until it alone outgrows a part; then it is cut before
    each of its H2 headings, and a section that still outgrows one is cut
    between the rows of its tables. A part that opens at a unit other than its
    page's first repeats the page's head, so every page in every part says
    what it is, and one that opens between two rows repeats the header row and
    the delimiter row of the table it continues (*repeat*).
    """

    route: str
    lines: tuple[str, ...]
    #: Whether the unit opens its page.
    first: bool
    #: Where the cut before it falls: between pages, at an H2, between rows.
    cut: str
    repeat: tuple[str, ...] = ()


#: An ATX H2 heading as CommonMark reads one: up to three spaces of indent, two
#: hashes, then a space, a tab or the end of the line. Four spaces of indent
#: make an indented code block, and ``##x`` is a paragraph, not a heading.
_H2 = re.compile(r" {0,3}##(?:[ \t]|$)")

#: A row of a GitHub table, as the Markdown writers write one.
_TABLE_ROW = re.compile(r" {0,3}\|")

#: The delimiter row under a table's header row.
_TABLE_DELIMITER = re.compile(r" {0,3}\|?(?: *:?-+:? *\|)+ *:?-*:? *$")


def _is_h2(line: str) -> bool:
    """Whether *line*, read outside code, is an H2 heading."""
    return _H2.match(line) is not None


def _sections(content: str) -> list[str]:
    """A text cut before each of its H2 headings.

    A heading is an H2 as CommonMark reads one (``_H2``). A ``## `` line
    inside a code fence is code, a Python comment for one, and never a cut;
    ``markdown_fences`` says which lines are code, as it does for every script
    that reads a page. The first section is whatever comes before the first
    H2.
    """
    lines = content.split("\n")
    sections: list[list[str]] = [[]]
    for line, code in zip(lines, code_lines(lines, kind="md"), strict=True):
        if not code and _is_h2(line) and sections[-1]:
            sections.append([])
        sections[-1].append(line)
    return ["\n".join(part) for part in sections]


def _section_units(unit: _Unit) -> list[_Unit]:
    """A page's unit cut before each of its H2 headings."""
    pieces = _sections("\n".join(unit.lines))
    return [
        _Unit(
            route=unit.route,
            lines=tuple(piece.split("\n")),
            first=unit.first and index == 0,
            cut=unit.cut if index == 0 else "section",
            repeat=unit.repeat if index == 0 else (),
        )
        for index, piece in enumerate(pieces)
    ]


def _row_units(unit: _Unit) -> list[_Unit]:
    """A unit cut between the rows of every table in it.

    A row opens a unit of its own unless it is the first row of its table,
    which stays with the header above it. Each unit opening on a row repeats
    that table's header row and delimiter row, so a part that opens there
    still says what its columns are.
    """
    lines = unit.lines
    code = list(code_lines(lines))
    starts: dict[int, tuple[str, ...]] = {}
    index = 0
    while index + 2 < len(lines):
        header, delimiter = lines[index], lines[index + 1]
        if (
            not code[index]
            and not code[index + 1]
            and _TABLE_ROW.match(header)
            and _TABLE_DELIMITER.match(delimiter)
        ):
            row = index + 3
            while row < len(lines) and not code[row] and _TABLE_ROW.match(lines[row]):
                starts[row] = (header, delimiter)
                row += 1
            index = row
        else:
            index += 1
    cuts = [0, *sorted(starts), len(lines)]
    return [
        _Unit(
            route=unit.route,
            lines=lines[begin:end],
            first=unit.first and begin == 0,
            cut=unit.cut if begin == 0 else "row",
            repeat=unit.repeat if begin == 0 else starts[begin],
        )
        for begin, end in zip(cuts, cuts[1:], strict=False)
        if end > begin
    ]


#: A footnote reference and a footnote definition, as GFM writes them.
_NOTE_REFERENCE = re.compile(r"\[\^([^\]\s]+)\](?!:)")
_NOTE_DEFINITION = re.compile(r"^ {0,3}\[\^([^\]\s]+)\]:", re.MULTILINE)


def _section_text(copy: Copy, units: Sequence[_Unit]) -> str:
    """A page as one part holds it: its head, then its run of *units*.

    A run that opens the page and holds no line is a page with nothing after
    its header, which a shard holds as the head alone, as it holds it whole.

    A part that cites a note the page defines in another part would leave its
    reader a mark with nothing under it, so it is refused by name: a cut
    between the rows of a table must not part a row from the note it cites.
    """
    lines = [] if units[0].first else [*units[0].repeat]
    for unit in units:
        lines += unit.lines
    if not lines:
        return copy.head
    text = "\n".join(lines)
    defined_here = set(_NOTE_DEFINITION.findall(text))
    defined_on_page = set(_NOTE_DEFINITION.findall(copy.rest))
    parted = sorted(
        (set(_NOTE_REFERENCE.findall(text)) & defined_on_page) - defined_here
    )
    if parted:
        notes = ", ".join(f"[^{label}]" for label in parted)
        msg = (
            f"{copy.route}: a part of its shard cites {notes} and another part "
            "holds the note; cut the page where no row is parted from its note"
        )
        raise ValueError(msg)
    return f"{copy.head}\n\n" + text


def _shard_head(title: str, note: str) -> str:
    """The lines every shard file opens with."""
    return f"# phonometry: {title}\n\nPart of {SITE_URL}/llms.txt. {note}\n\n---\n"


def _shard_file(head: str, sections: Iterable[str]) -> str:
    """A shard: its head, then each page, each closed by :data:`PAGE_END`."""
    return head + "".join(f"\n{section}{PAGE_END}" for section in sections)


def _cut_note(*, single_page: bool, cuts: Iterable[str]) -> str:
    """How a shard in parts was cut, in the words of its head."""
    if single_page:
        words = {
            "section": "at its own sections",
            "row": "between the rows of its tables",
        }
    else:
        words = {
            "page": "between its pages",
            "section": "at the sections of a page too long for one",
            "row": "between the rows of a table too long for one",
        }
    used = [
        words[cut]
        for cut in ("page", "section", "row")
        if cut in set(cuts) and cut in words
    ]
    if len(used) > 1:
        return ", ".join(used[:-1]) + " and " + used[-1]
    return used[0] if used else words[next(iter(words))]


def _part_head(
    *,
    slug: str,
    title: str,
    number: int,
    count: int,
    single_page: bool,
    cuts: Iterable[str],
) -> str:
    """The head of one part of a shard cut into *count*."""
    urls = ", ".join(_shard_url(name) for name in _part_names(slug, count))
    what = "One page" if single_page else "The pages of this area"
    note = (
        f"{what} in {count} parts, cut {_cut_note(single_page=single_page, cuts=cuts)} so that "
        f"each fits one fetch: {urls}."
    )
    return _shard_head(_part_label(title, number, count), note)


def _starts(base: Sequence[int], extra: Sequence[int], capacity: int) -> list[int]:
    """Where each part begins when units fill parts in order up to *capacity*.

    A part costs the units it holds (*base*) and, when it opens in the middle
    of a page, what that opening repeats (*extra*).
    """
    starts = [0]
    used = extra[0]
    for index, size in enumerate(base):
        if index > starts[-1] and used + size > capacity:
            starts.append(index)
            used = extra[index]
        used += size
    return starts


def _balanced_starts(
    base: Sequence[int], extra: Sequence[int], count: int, capacity: int
) -> list[int]:
    """The cut into at most *count* parts whose largest part is smallest.

    Filling each part to the brim before opening the next would leave a stub
    at the end, and move every cut whenever a line is added near the top of
    the page. The smallest capacity that still needs no more parts is found by
    bisection; it is never above *capacity*, which already needs *count*.
    """
    low = max(size + more for size, more in zip(base, extra, strict=True))
    high = capacity
    while low < high:
        middle = (low + high) // 2
        if len(_starts(base, extra, middle)) <= count:
            high = middle
        else:
            low = middle + 1
    return _starts(base, extra, high)


def _unit_name(unit: _Unit) -> str:
    """What a unit is, for a refusal that has to name it."""
    first = next((line for line in unit.lines if line.strip()), "")
    if unit.cut == "row":
        return f"the table row {first[:80]!r}"
    if _is_h2(first):
        return f"its section {first.strip()!r}"
    return "the text before its first H2"


def _oversized(slug: str, unit: _Unit, size: int, room: int) -> str:
    """Why a shard cannot be cut into parts that fit, naming the culprit."""
    return (
        f"generate_llms.py: {unit.route} cannot be cut to fit llms-{slug}.txt: "
        f"{_unit_name(unit)} alone takes {size:,} bytes, more than the {room:,} "
        f"a part has room for under the {SHARD_LIMIT_BYTES:,} byte budget of one "
        "fetch. Divide it under H2 headings of its own; do not raise "
        "SHARD_LIMIT_BYTES."
    )


def _shard_parts(slug: str, title: str, routes: Sequence[str]) -> tuple[str, ...]:
    """A shard's text: one file, or numbered parts when it outgrows one fetch.

    The parts are as few as fit the budget and as even as the cuts allow. A
    shard of several pages is cut between its pages; a page that alone
    outgrows a part, there or in a shard of its own, is cut before its H2
    headings, and a section that still outgrows one between the rows of its
    tables. Each part is a whole shard: its head names every part, and every
    page in it opens with its own head, so a passage read from any part can
    still be cited back. A table row too long by itself is refused by name
    rather than cut mid-text.

    Where the cuts fall is decided on the pages measured with their dated
    header lines whether those are there or not (:func:`_measured_head`), so
    a dump with dates and one without cut every shard at the same places.
    """
    copies = {route: _copy(route) for route in routes}
    single = _shard_head(title, "Full text of the pages in this area.")
    whole = _shard_file(single, (copies[route].text for route in routes))
    measured = len(single.encode("utf-8")) + sum(
        2
        + _measured_head(copies[route].head)
        + len(PAGE_END)
        + _lines_bytes(copies[route].rest.split("\n") if copies[route].rest else ())
        for route in routes
    )
    if measured <= SHARD_LIMIT_BYTES:
        return (whole,)

    units = [
        _Unit(
            route=route,
            lines=tuple(copy.rest.split("\n")) if copy.rest else (),
            first=True,
            cut="page",
        )
        for route, copy in copies.items()
    ]
    overhead = {
        route: 2 + _measured_head(copy.head) + len(PAGE_END)
        for route, copy in copies.items()
    }
    single_page = len(routes) == 1

    def costs(units: Sequence[_Unit]) -> tuple[list[int], list[int]]:
        base = [
            _lines_bytes(unit.lines) + (overhead[unit.route] if unit.first else 0)
            for unit in units
        ]
        extra = [
            0 if unit.first else overhead[unit.route] + _lines_bytes(unit.repeat)
            for unit in units
        ]
        return base, extra

    count = 2
    while True:
        # The longest head a part of this count can have: its number at the
        # count, and a note naming every kind of cut.
        head = _part_head(
            slug=slug,
            title=title,
            number=count,
            count=count,
            single_page=single_page,
            cuts=("page", "section", "row"),
        )
        room = SHARD_LIMIT_BYTES - len(head.encode("utf-8"))
        refined: list[_Unit] = []
        for unit in units:
            pieces = [unit]
            for finer in (_section_units, _row_units):
                base, extra = costs(pieces)
                if all(
                    size + more <= room for size, more in zip(base, extra, strict=True)
                ):
                    break
                pieces = [
                    piece
                    for whole_unit, size, more in zip(pieces, base, extra, strict=True)
                    for piece in (
                        finer(whole_unit) if size + more > room else [whole_unit]
                    )
                ]
            base, extra = costs(pieces)
            for piece, size, more in zip(pieces, base, extra, strict=True):
                if size + more > room:
                    raise SystemExit(_oversized(slug, piece, size + more, room))
            refined += pieces
        units = refined
        base, extra = costs(units)
        needed = len(_starts(base, extra, room))
        if needed <= count:
            break
        count = needed
    starts = [*_balanced_starts(base, extra, count, room), len(units)]
    count = len(starts) - 1
    cuts = [units[start].cut for start in starts[1:-1]]
    parts = []
    for number, (begin, end) in enumerate(
        zip(starts, starts[1:], strict=False), start=1
    ):
        sections = []
        run: list[_Unit] = []
        for unit in units[begin:end]:
            if run and unit.route != run[0].route:
                sections.append(_section_text(copies[run[0].route], run))
                run = []
            run.append(unit)
        sections.append(_section_text(copies[run[0].route], run))
        head = _part_head(
            slug=slug,
            title=title,
            number=number,
            count=count,
            single_page=single_page,
            cuts=cuts,
        )
        parts.append(_shard_file(head, sections))
    return tuple(parts)


def _published(shards: Mapping[str, tuple[str, ...]]) -> dict[str, str]:
    """Every file the shards publish, by the name ``llms-`` precedes.

    Refuses two shards that would write one file: a shard ``a`` in two parts
    and a shard ``a-1`` would otherwise overwrite each other in silence.
    """
    files: dict[str, str] = {}
    for slug, parts in shards.items():
        for name, text in zip(_part_names(slug, len(parts)), parts, strict=True):
            if name in files:
                msg = (
                    f"generate_llms.py: two shards publish llms-{name}.txt; "
                    f"rename the shard {slug} or the one it collides with."
                )
                raise SystemExit(msg)
            files[name] = text
    return files


def _index_order(index: str, members: Iterable[str]) -> list[str]:
    """Pages in the order an index page links them, the rest sorted after."""
    pool = sorted(members)
    ordered = _linked(_copy(index).text, pool) if index in _dump() else []
    return ordered + [route for route in pool if route not in ordered]


def _shard_plan() -> list[tuple[str, str, list[str]]]:
    """Every shard as ``(slug, label, routes)``, in the order the index lists them.

    The order is the reading order: the start pages, the upgrade guide, the
    theory, the topics as the site lists them, the reference, the glossary,
    the conformance report, the errata register and the catalogues.
    llms-full.txt carries the pages in this order too.
    """
    carried = _routes()
    plan: list[tuple[str, str, list[str]]] = []

    # Theory used to travel inside the start shard: six mirror pages with
    # eighteen figures pushed llms-start.txt itself over budget. It gets its
    # own shard instead of a cut, since a client after the getting-started
    # page has no reason to also fetch the physics. The migration guide gets
    # the same treatment: one row per 4.0 break, it alone took llms-start.txt
    # over budget, and a client after the getting-started page has no reason
    # to fetch every renamed parameter.
    start = [
        *(["start"] if "start" in carried else []),
        *(route for route in START_ROUTES if route != UPGRADING_ROUTE),
    ]
    start += [
        route
        for route in carried
        if route.startswith("start/")
        and route not in start
        and route != UPGRADING_ROUTE
    ]
    plan.append(("start", "Start here", start))
    if UPGRADING_ROUTE in carried:
        plan.append(("upgrading", UPGRADING_TITLE, [UPGRADING_ROUTE]))
    theory = [route for route in carried if route.startswith("reference/theory")]
    if theory:
        plan.append(("theory", "Theory and reference", theory))

    manual_split_slugs = {
        slug for splits in MANUAL_SPLITS.values() for slug, _label, _leaves in splits
    }
    members = _shard_members()
    topics = _topic_shards(members)
    for slug in [*topics, *(slug for slug in members if slug not in topics)]:
        overview = _shard_folders().get(slug, slug)
        # A carved-out shard (see MANUAL_SPLITS) has no overview page of its
        # own; the folder it names already opened its primary shard.
        include_overview = overview in carried and slug not in manual_split_slugs
        routes = [*([overview] if include_overview else []), *members[slug]]
        if routes:
            label = "Other guides" if slug == "other" else _shard_label(slug)
            plan.append((slug, label, routes))

    # The reference pages that are neither theory (its own shard) nor a
    # topic's: the reference overview, the bibliography, the indexes of the
    # report fiches and the catalogues, and what the build does to stay
    # reproducible. The glossary travels on its own: with the bibliography
    # beside it the reference shard reached the fetch budget, and the two
    # answer different questions. The bibliography does too: once it listed
    # every work the pages cite, each with every page that cites it, it alone
    # outgrew the budget, and a shard of one page is cut at its own headings
    # (its areas) into numbered parts. So does the conformance report, cut at
    # its domains, and the errata register, its index first and then its
    # families, cut between them.
    pages = _dump()
    own = {GLOSSARY_ROUTE, BIBLIOGRAPHY_ROUTE, CONFORMANCE_ROUTE, ERRATA_ROUTE}
    reference = [
        route
        for route in carried
        if (route == "reference" or route.startswith("reference/"))
        and not route.startswith("reference/theory")
        and pages[route].kind == "guide"
        and route not in own
    ]
    if reference:
        plan.append(("reference", "Reference", reference))
    if BIBLIOGRAPHY_ROUTE in carried:
        plan.append(("bibliography", "Bibliography", [BIBLIOGRAPHY_ROUTE]))
    if GLOSSARY_ROUTE in carried:
        plan.append(("glossary", "Glossary of quantities", [GLOSSARY_ROUTE]))
    if CONFORMANCE_ROUTE in carried:
        plan.append(
            ("conformance", _page_title(CONFORMANCE_ROUTE), [CONFORMANCE_ROUTE])
        )
    families = [route for route in carried if pages[route].kind == "errata-family"]
    if ERRATA_ROUTE in carried or families:
        plan.append(
            (
                "errata",
                _page_title(ERRATA_ROUTE) if ERRATA_ROUTE in carried else "Errata",
                [
                    *([ERRATA_ROUTE] if ERRATA_ROUTE in carried else []),
                    *_index_order(ERRATA_ROUTE, families),
                ],
            )
        )
    catalogues = [route for route in carried if pages[route].kind == "catalogue"]
    plan += [
        (f"catalogues-{route.rsplit('/', 1)[1]}", _page_title(route), [route])
        for route in _index_order(CATALOGUES_ROUTE, catalogues)
    ]
    return plan


def _check_every_page_in_one_shard(plan: Sequence[tuple[str, str, list[str]]]) -> None:
    """Every page these files carry is in exactly one shard.

    A page that falls between the buckets is how the bibliography went
    missing; one in two shards would be fetched twice and counted twice. The
    set compared is what the plan holds, not a second prediction of it.
    """
    seen: dict[str, str] = {}
    twice = []
    for slug, _label, routes in plan:
        for route in routes:
            if route in seen:
                twice.append(f"{route} (llms-{seen[route]} and llms-{slug})")
            seen[route] = slug
    dropped = sorted(set(_routes()) - set(seen))
    strays = sorted(set(seen) - set(_routes()))
    problems = []
    if dropped:
        problems.append("page(s) in no shard: " + ", ".join(dropped))
    if twice:
        problems.append("page(s) in two shards: " + ", ".join(twice))
    if strays:
        problems.append(
            "route(s) in a shard and with no copy in the dump: " + ", ".join(strays)
        )
    if problems:
        raise SystemExit("generate_llms.py: " + "; ".join(problems))


def build_shards(
    plan: Sequence[tuple[str, str, list[str]]] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Shard slug -> its text, in one file or in parts."""
    plan = _shard_plan() if plan is None else plan
    _check_every_page_in_one_shard(plan)
    return {slug: _shard_parts(slug, label, routes) for slug, label, routes in plan}


def build_llms_full(llms_txt: str, plan: Sequence[tuple[str, str, list[str]]]) -> str:
    """The index, then every page these files carry, whole, in reading order."""
    return f"{llms_txt}\n---\n" + "".join(
        f"\n{_copy(route).text}{PAGE_END}"
        for _slug, _label, routes in plan
        for route in routes
    )


def _check_readme_covers_the_mirror() -> None:
    """docs/README.md links every mirror guide page.

    The README is the GitHub front door of the docs, kept by hand, and three
    pages went missing from it inside one week of merges: nothing looked. The
    overview index files are exempt because the README's section structure is
    its own index of the folders, which
    ``mirror_overviews.py --check`` asserts separately (it requires every
    generated ``index.md`` to be linked from the README).
    """
    readme = (DOCS / "README.md").read_text(encoding="utf-8")
    missing = [
        name
        for name in _mirror_pages()
        if not name.endswith("/index.md")
        and not name.startswith("reference/api")
        and f"({name})" not in readme
    ]
    if missing:
        raise SystemExit(
            "generate_llms.py: docs/README.md does not link " + ", ".join(missing)
        )


def _check_index_covers_the_site(llms_txt: str) -> None:
    """Every English page of the site but the landing page is linked from the index.

    The index used to name the pages docs/ mirrors and a hand-kept few, so the
    96 errata families, the catalogues, the task index and two section pages
    were in the sitemap and nowhere in the file an agent reads first. The set
    is the site's own (:func:`_content_routes`), read without a build, as this
    runs in ``make llms`` and in CI before any build.
    """
    linked = set(re.findall(rf"\]\({re.escape(SITE_URL)}/((?:[^)\s]*?))/?\)", llms_txt))
    missing = sorted(route for route in _content_routes() - {""} if route not in linked)
    if missing:
        msg = (
            f"generate_llms.py: llms.txt links no line to {len(missing)} English "
            "page(s) of the site: " + ", ".join(missing) + ". List each where its "
            "section of the index belongs."
        )
        raise SystemExit(msg)


def _check_index_budget(llms_txt: str) -> None:
    """Fail when ``llms.txt`` is over :data:`LLMS_TXT_LIMIT_BYTES`."""
    size = len(llms_txt.encode("utf-8"))
    if size > LLMS_TXT_LIMIT_BYTES:
        msg = (
            f"generate_llms.py: llms.txt is {size} bytes, over the "
            f"{LLMS_TXT_LIMIT_BYTES}-byte budget of an index a client reads whole"
        )
        raise SystemExit(msg)


def _check_shard_budget(sizes: dict[str, int]) -> None:
    """Fail the run if any shard exceeds :data:`SHARD_LIMIT_BYTES`.

    This used to be a printed note with exit 0, so llms-start.txt and
    llms-buildings-insulation.txt sat over budget for weeks with a green CI: a
    client that truncates at a few hundred kilobytes read a partial shard and
    nothing here ever said so. The budget is not negotiable (see its own
    docstring). A shard does not reach this check over the budget:
    :func:`_shard_parts` has already cut it into parts, or refused the piece
    that does not fit any part; this holds the files written to that.
    """
    oversized = sorted(
        (slug, size) for slug, size in sizes.items() if size > SHARD_LIMIT_BYTES
    )
    if not oversized:
        return
    detail = "\n".join(
        f"  llms-{slug}.txt is {size:,} bytes, {size - SHARD_LIMIT_BYTES:,} over "
        f"the {SHARD_LIMIT_BYTES:,} byte budget"
        for slug, size in oversized
    )
    raise SystemExit(
        "generate_llms.py: shard(s) exceed the fetch budget:\n"
        + detail
        + "\nCut the shard narrower; do not raise SHARD_LIMIT_BYTES."
    )


def _write_build(
    llms: str, plan: Sequence[tuple[str, str, list[str]]], files: Mapping[str, str]
) -> None:
    """Writes what the site publishes: llms.txt, llms-full.txt and every shard.

    Every shard this run does not produce is removed. Regrouping a section
    renames its shard, and an orphan left behind would keep serving text that
    llms.txt no longer indexes, silently and indefinitely; a shard cut into
    parts retires its single file the same way, and the parts it no longer
    needs. The root-level sweep retires shards left at the site root by an
    older layout.
    """
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "llms.txt").write_text(llms, encoding="utf-8", newline="\n")
    (PUBLIC / "llms-full.txt").write_text(
        build_llms_full(llms, plan), encoding="utf-8", newline="\n"
    )
    SHARDS_DIR.mkdir(parents=True, exist_ok=True)
    keep = {f"llms-{name}.txt" for name in files}
    for path in SHARDS_DIR.glob("llms-*.txt"):
        if path.name not in keep:
            path.unlink()
            print(f"  removed stale shard llms/{path.name}")
    for path in PUBLIC.glob("llms-*.txt"):
        if path.name != "llms-full.txt":
            path.unlink()
            print(f"  removed stale shard {path.name}")
    for name, text in files.items():
        (SHARDS_DIR / f"llms-{name}.txt").write_text(
            text, encoding="utf-8", newline="\n"
        )


def main(argv: Sequence[str] | None = None) -> None:
    # The dump every function reads is chosen once, here, by the command line.
    global PAGES
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "--pages",
        type=pathlib.Path,
        default=PAGES,
        help="the dump site/scripts/agent-md.mjs --dump wrote (default: build/agent-md)",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="write llms.txt, llms-full.txt and the shards into site/public "
        "for the site build, instead of llms.txt at the repository root",
    )
    args = parser.parse_args(argv)
    PAGES = args.pages.resolve()

    _check_areas_cover_the_tree()
    _check_readme_covers_the_mirror()
    _check_dump_matches_the_tree()
    version = _version()
    plan = _shard_plan()
    shards = build_shards(plan)
    files = _published(shards)
    llms = build_llms_txt(
        version,
        {slug: _part_names(slug, len(parts)) for slug, parts in shards.items()},
        plan,
    )
    _check_index_covers_the_site(llms)
    _check_index_budget(llms)
    if args.build:
        _write_build(llms, plan, files)
        where = "site/public"
    else:
        INDEX.write_text(llms, encoding="utf-8", newline="\n")
        where = "llms.txt"
    print(
        f"llms.txt regenerated (v{version}) into {where}: {len(_routes())} pages "
        f"in {len(shards)} shards ({len(files)} files), "
        f"{len(_api_routes())} API pages listed as optional."
    )
    _check_shard_budget(
        {name: len(text.encode("utf-8")) for name, text in files.items()}
    )


if __name__ == "__main__":
    main()
