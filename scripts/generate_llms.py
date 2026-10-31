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
documentation tree now, and :func:`_routes` raises if a page cannot be placed,
so the same drift cannot happen quietly again.

Three kinds of artifact are produced:

``llms.txt``
    The index. Every page, grouped by area, plus the evidence pages, the
    Spanish tree and the API reference as an Optional section.
``llms/llms-<area>.txt``
    One shard per documented area, each small enough to survive a single fetch.
    ``llms-full.txt`` is roughly 291k tokens, so a client that truncates at a
    few hundred kilobytes (most of them do) reads the first few metrology
    guides and nothing else, which is the worst possible sample: it looks like
    the old narrow library. A shard that holds one page too long for a single
    fetch travels in numbered parts instead, ``llms-<area>-1.txt``,
    ``llms-<area>-2.txt`` and so on, cut at the page's own H2 headings (see
    :func:`_page_parts`).
``llms-full.txt``
    The complete concatenation, kept for clients that can take it.

The two index-level artifacts live at the repo root and are published to the
site root by site/scripts/copy-llms.mjs (prebuild). The shards are written
straight into site/public/llms/, which Astro serves verbatim under
``/llms/``, so the site root holds exactly the two files the llms.txt
convention names. Deterministic: regenerate with ``make llms``.
"""

from __future__ import annotations

import functools
import itertools
import json
import pathlib
import re
import subprocess
import tomllib
from typing import TYPE_CHECKING

from markdown_fences import code_lines

if TYPE_CHECKING:
    from collections.abc import Mapping

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


@functools.cache
def _ignored_paths() -> frozenset[str]:
    """Everything under docs/ that git ignores, as repo-relative paths."""
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "--",
            "docs",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    return frozenset(result.stdout.split())


def _git_ignored(path: pathlib.Path) -> bool:
    """Is this file one git ignores (a local plan, a scratch note)?"""
    return path.relative_to(ROOT).as_posix() in _ignored_paths()


CONTENT = ROOT / "site" / "src" / "content" / "docs"
#: Where the per-area shards live. Everything under site/public is served
#: verbatim at the site root, so these publish at /llms/llms-<area>.txt and
#: the site root keeps exactly llms.txt and llms-full.txt.
SHARDS_DIR = ROOT / "site" / "public" / "llms"
SITE_URL = "https://docs.jmrp.io/phonometry"
REPO_URL = "https://github.com/jmrplens/phonometry"
DOI = "10.5281/zenodo.21215280"

#: Shard budget. Comfortably under the truncation limit of the AI fetch tools
#: that cap response size, with room for a page to grow. Enforced: main() exits
#: non-zero if a shard is over it (see :func:`_check_shard_budget`). A shard
#: exactly at the limit passes; only strictly over fails, both here and in the
#: message it raises. A shard of a single page over it is cut into parts at the
#: page's H2 headings rather than refused (see :func:`_page_parts`).
SHARD_LIMIT_BYTES = 200_000

#: The title of the upgrade guide's shard, in its head and in the index.
UPGRADING_TITLE = "Upgrading from 3.3 to 4.0"

#: The glossary page, which has a shard of its own (see :func:`build_shards`).
GLOSSARY_ROUTE = "reference/glossary"

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
    "start/why-phonometry",
    "start/upgrading",
    "start/about",
    "start/support",
)

#: The start page that travels in a shard of its own (see :func:`build_shards`).
UPGRADING_ROUTE = "start/upgrading"


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


@functools.cache
def _routes() -> list[tuple[str, str]]:
    """Every docs/ page as ``(path under docs/, site route)``.

    The mirror is laid out like the site, so the route is the path: the page
    at ``docs/signals/filters/filter-banks.md`` is published at
    ``/signals/filters/filter-banks/``. Raises if a mirror page has no page on
    the site, which would otherwise vanish from llms.txt silently, exactly how
    the hand-kept list rotted.
    """
    pages: list[tuple[str, str]] = []
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
        # site page and stays out of llms.txt by design.
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
        pages.append((path.relative_to(DOCS).as_posix(), route))
    if unmapped:
        raise SystemExit(
            "generate_llms.py: no site page for "
            + ", ".join(f"docs/{route}.md" for route in unmapped)
            + ". The mirror mirrors the site: move the file to the route its "
            "page has, or delete it if the page is gone."
        )
    return pages


def _api_routes() -> list[str]:
    """Every generated API reference page route, English tree."""
    api = CONTENT / "reference" / "api"
    if not api.is_dir():
        return []
    return sorted(
        path.relative_to(CONTENT).with_suffix("").as_posix()
        for path in api.rglob("*.md*")
        if path.stem != "index"
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


def _linked_guides(overview: pathlib.Path, guides: set[str], folder: str) -> list[str]:
    """Guide routes an overview links, in order, restricted to its own folder.

    The prose gives the reading order, which is the point of reading it, but an
    overview also cross-references guides that live elsewhere. Membership is
    structural: a page belongs to the folder it is in, and only its own
    overview can order it.
    """
    text = overview.read_text(encoding="utf-8") if overview.exists() else ""
    return [
        route
        for route in dict.fromkeys(
            re.findall(r"/phonometry/([a-z0-9-]+(?:/[a-z0-9-]+)*)/", text)
        )
        if route in guides and route.rsplit("/", 1)[0] == folder
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
    mentioned = [
        folder
        for folder in dict.fromkeys(
            re.findall(r"/phonometry/([a-z0-9-]+(?:/[a-z0-9-]+)*)/", text)
        )
        if folder in folders
    ]
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


#: Manual carve-outs from a folder's own shard, for a folder whose guides are
#: still over the fetch budget after subgroup splitting. Two folders need one,
#: both because they have no subgroups of their own to divide by (unlike
#: ``buildings/rooms`` or ``buildings/design``, which already get a shard each
#: above). Each split follows a grouping the domain already makes rather than
#: a cut chosen to fit the budget, so a reader fetching one shard gets a
#: coherent set of guides and not an arbitrary half.
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

    The index groups by the ten topics a reader recognises, but several of
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


def _page_title(path: pathlib.Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _shard_label(slug: str) -> str:
    """The human name of a shard: the H1 of the overview it opens with.

    ``slug.capitalize()`` named none of the sections the site shows: it said
    "Signal metrology" where the site says "Calibration and uncertainty" and
    "Buildings rooms" where it says "Room acoustics". The overview's own title
    is the name a reader of the site would recognise, and the mirror carries it
    now.
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
    index = DOCS / folder / "index.md"
    if index.exists():
        return _page_title(index)
    return slug.replace("-", " ").capitalize()


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
            "`[torch]` adds. The base install computes every metric on NumPy and "
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
            "(no system dependencies), remember integer audio (e.g. wavfile.read "
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


@functools.cache
def _route_files() -> dict[str, str]:
    """Site route -> its page under docs/."""
    return {route: name for name, route in _routes()}


def _page_entry(route: str) -> str | None:
    """The index line of one page, or None when it has no mirror page."""
    name = _route_files().get(route)
    if name is None:
        return None
    return f"- [{_page_title(DOCS / name)}]({SITE_URL}/{route}/)"


def _start_section() -> list[str]:
    lines = ["## Start here", ""]
    for route in START_ROUTES:
        entry = _page_entry(route)
        if entry is None:
            # These are listed by hand, so an unresolvable one is always a
            # bug; the About page went missing this way once, silently.
            msg = (
                f"generate_llms.py: START_ROUTES names {route}, "
                "which has no mirror page"
            )
            raise SystemExit(msg)
        lines.append(entry)
    return [
        *lines,
        f"- [Guides index]({SITE_URL}/start/guides/)",
        f"- [Glossary of quantities]({SITE_URL}/reference/glossary/)",
        "",
    ]


def _area_section(
    slug: str, routes: list[str], shard_files: Mapping[str, tuple[str, ...]]
) -> list[str]:
    """One topic of the index: its overview, then its guides, run by shard."""
    lines = [f"## {dict(AREAS).get(slug, 'Other guides')}", ""]
    if slug != "other":
        lines.append(f"- [Overview]({SITE_URL}/{slug}/)")
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
                    f"- [Overview]({SITE_URL}/{folder}/) · "
                    + _full_text_links(shard_files.get(group, (group,)))
                ),
            ]
        lines += [
            entry for route in grouped.get(group, []) if (entry := _page_entry(route))
        ]
    lines.append("")
    return lines


def _reference_section(shard_files: Mapping[str, tuple[str, ...]]) -> list[str]:
    lines = [
        "## Theory and reference",
        "",
        (
            "The theory pages travel in their own shard "
            f"({_shard_urls(shard_files, 'theory')}), the glossary in another "
            f"({_shard_urls(shard_files, 'glossary')}), and the rest of the "
            f"reference in {_shard_urls(shard_files, 'reference')}."
        ),
        "",
    ]
    lines += [
        entry
        for route in sorted(
            route
            for route in _route_files()
            if route.startswith("reference/") and route != "reference/why-phonometry"
        )
        if (entry := _page_entry(route))
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
        "- [Licence: MIT](https://opensource.org/licenses/MIT)",
        "",
    ]


def _topic_shards(shard_slugs: tuple[str, ...]) -> list[str]:
    """The shards of the topics, in the order the site lists them.

    Grouped by topic, the topic's own shard first, so the list reads like the
    navigation rather than like a sort key. Within a topic the subgroups come
    in the order the topic overview teaches them, matching the navigation;
    alphabetical-by-slug put Calibration before Spectra in a topic whose
    overview teaches them the other way round. The slugs are the shards
    actually built this run: a hand-kept list here published a link to a shard
    that a content move could stop producing.
    """
    folders = _shard_folders()
    ordered: list[str] = []
    for topic, _label in AREAS:
        nav_order = {folder: rank for rank, folder in enumerate(_subgroups(topic))}
        ordered += [slug for slug in shard_slugs if slug == topic]
        ordered += sorted(
            (slug for slug in shard_slugs if slug.startswith(f"{topic}-")),
            key=lambda slug: (
                nav_order.get(folders.get(slug, ""), len(nav_order)),
                slug,
            ),
        )
    return ordered


def _full_text_section(shard_files: Mapping[str, tuple[str, ...]]) -> list[str]:
    intro = "One file per area, each small enough to fetch whole."
    if any(len(files) > 1 for files in shard_files.values()):
        intro += (
            " A page too long for one fetch travels in numbered parts, cut at "
            "its own sections."
        )
    intro += (
        " `llms-full.txt` is the complete concatenation and is far too large "
        "for a single fetch in most clients."
    )
    lines = ["## Full text", "", intro, ""]
    lines += _full_text_entries("Start here", shard_files.get("start", ("start",)))
    # "upgrading" and "theory" are listed by hand, next to "start": none is a
    # topic, so the walk of the topics below would never place them.
    for slug, label in (
        ("upgrading", UPGRADING_TITLE),
        ("theory", "Theory and reference"),
    ):
        if slug in shard_files:
            lines += _full_text_entries(label, shard_files[slug])
    topics = _topic_shards(tuple(shard_files))
    lines += [
        entry
        for slug in topics
        for entry in _full_text_entries(_shard_label(slug), shard_files[slug])
    ]
    listed = {"start", "upgrading", "theory", *topics}
    lines += [
        entry
        for slug, files in shard_files.items()
        if slug not in listed
        for entry in _full_text_entries(
            "Other guides" if slug == "other" else _shard_label(slug), files
        )
    ]
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
        "## Optional",
        "",
        (
            "The generated API reference, one page per module. Fetch these only when "
            "a specific signature is needed; the guides above explain the same "
            "functions in context."
        ),
        "",
        f"- [API reference index]({SITE_URL}/reference/api/)",
    ]
    lines += [
        f"- [{route.removeprefix('reference/api/')}]({SITE_URL}/{route}/)"
        for route in _api_routes()
    ]
    lines.append("")
    return lines


def build_llms_txt(version: str, shard_files: Mapping[str, tuple[str, ...]]) -> str:
    """The index, *shard_files* naming the files each shard published.

    A shard in one piece names one file; a page cut into parts names one per
    part (see :func:`_part_names`), and the index lists every one of them.
    """
    lines = _summary(version)
    lines += _start_section()
    for slug, routes in _area_members().items():
        lines += _area_section(slug, routes, shard_files)
    lines += _reference_section(shard_files)
    lines += _provenance_section()
    lines += _full_text_section(shard_files)
    lines += _closing_sections()
    return "\n".join(lines)


def _absolutize_links(content: str, md_name: str) -> str:
    """Rewrite mirror-relative markdown links to canonical absolute URLs.

    The shards are served as flat text, so a link relative to the page that
    holds it (``[x](../filters/filter-banks.md#anchor)``) would not resolve.
    The mirror is laid out like the site, so the target resolved against the
    page's own folder is the route, with the two generated documents at the
    repository root transplanted into the routes that publish them.
    """
    here = pathlib.PurePosixPath(md_name).parent
    #: Mirror page at the repository root -> the route that publishes it.
    transplanted = {
        "README": "",
        "CONFORMANCE": "reference/conformance",
        "ERRATA": "reference/errata",
        "ERRATA.es": "es/reference/errata",
    }

    def repl(match: re.Match[str]) -> str:
        target, anchor = match.group(1), match.group(2) or ""
        resolved = (here / target).as_posix()
        parts: list[str] = []
        for step in resolved.split("/"):
            if step == "..":
                if parts:
                    parts.pop()
            elif step not in (".", ""):
                parts.append(step)
        route = "/".join(parts).removesuffix(".md").removesuffix("/index")
        if route == "CONTRIBUTING":
            return f"]({REPO_URL}/blob/main/CONTRIBUTING.md{anchor})"
        route = transplanted.get(route, route)
        suffix = f"{route}/" if route else ""
        return f"]({SITE_URL}/{suffix}{anchor})"

    return re.sub(r"\]\(((?:\.\./)*[\w./-]+\.md)(#[\w-]+)?\)", repl, content)


def _page_text(md_name: str) -> str:
    """One page as the artifacts carry it: no index backlink, absolute links."""
    content = (DOCS / md_name).read_text(encoding="utf-8")
    # Drop the docs-index backlink line; keep everything else verbatim.
    content = "\n".join(
        line
        for line in content.splitlines()
        if not line.startswith("← [Documentation index]")
    ).strip()
    return _absolutize_links(content, md_name)


def _attributed(md_name: str, route: str, content: str) -> str:
    """Page text ready to concatenate: attribution header, then the text."""
    # A plain "Source:" line as well as the HTML comment: markdown-to-text
    # pipelines routinely strip comments, and a passage extracted with its
    # attribution stripped is a passage that cannot be cited back.
    header = (
        f"<!-- source: docs/{md_name} | canonical: {SITE_URL}/{route}/ -->\n"
        f"Source: {SITE_URL}/{route}/\n"
    )
    return f"\n{header}\n{content}\n\n---\n"


def _body(md_name: str, route: str) -> str:
    """One page, ready to concatenate: attribution header then verbatim text."""
    return _attributed(md_name, route, _page_text(md_name))


def _shard_head(title: str, note: str) -> list[str]:
    """The lines every shard file opens with."""
    return [
        f"# phonometry: {title}",
        "",
        f"Part of {SITE_URL}/llms.txt. {note}",
        "",
        "---",
    ]


def _shard_text(title: str, pages: list[tuple[str, str]]) -> str:
    """A shard in one file: its head, then each ``(file, route)`` page in turn."""
    return "\n".join(
        [
            *_shard_head(title, "Full text of the pages in this area."),
            *(_body(name, route) for name, route in pages),
        ]
    )


#: An ATX H2 heading as CommonMark reads one: up to three spaces of indent, two
#: hashes, then a space, a tab or the end of the line. Four spaces of indent
#: make an indented code block, and ``##x`` is a paragraph, not a heading.
_H2 = re.compile(r" {0,3}##(?:[ \t]|$)")


def _is_h2(line: str) -> bool:
    """Whether *line*, read outside code, is an H2 heading."""
    return _H2.match(line) is not None


def _sections(content: str) -> list[str]:
    """A page cut before each of its H2 headings.

    A heading is an H2 as CommonMark reads one (``_H2``). A ``## `` line
    inside a code fence is code, a Python comment for one, and never a cut; ``markdown_fences`` says which lines are code, as it does for
    every script that reads a page. The first section is whatever comes before
    the first H2: the page title and its introduction.
    """
    lines = content.splitlines()
    sections: list[list[str]] = [[]]
    for line, code in zip(lines, code_lines(lines), strict=True):
        if not code and _is_h2(line):
            sections.append([])
        sections[-1].append(line)
    return ["\n".join(part) for part in sections if any(map(str.strip, part))]


def _starts(sizes: list[int], capacity: int) -> list[int]:
    """Where each part begins when sections fill parts in order up to *capacity*."""
    starts = [0]
    used = 0
    for index, size in enumerate(sizes):
        if used and used + size > capacity:
            starts.append(index)
            used = 0
        used += size
    return starts


def _balanced_starts(sizes: list[int], count: int, capacity: int) -> list[int]:
    """The cut into at most *count* parts whose largest part is smallest.

    Filling each part to the brim before opening the next would leave a stub
    at the end, and move every cut whenever a line is added near the top of
    the page. The smallest capacity that still needs no more parts is found by
    bisection; it is never above *capacity*, which already needs *count*.
    """
    low, high = max(sizes), capacity
    while low < high:
        middle = (low + high) // 2
        if len(_starts(sizes, middle)) <= count:
            high = middle
        else:
            low = middle + 1
    return _starts(sizes, low)


def _render_part(
    *, slug: str, title: str, page: tuple[str, str], number: int, count: int, text: str
) -> str:
    """One part of a page cut into *count*: its head, then its sections."""
    urls = ", ".join(_shard_url(name) for name in _part_names(slug, count))
    note = (
        f"One page in {count} parts, cut at its own sections so that each fits "
        f"one fetch: {urls}."
    )
    md_name, route = page
    return "\n".join(
        [
            *_shard_head(_part_label(title, number, count), note),
            _attributed(md_name, route, text),
        ]
    )


def _oversized_section(
    *, slug: str, md_name: str, shard_bytes: int, sections: list[str], room: int
) -> str:
    """Why a page cannot be cut into parts that fit, naming the culprit.

    The size quoted is the shard's, *shard_bytes*, not the source file's: the
    head, the attribution and the absolute links the shard adds can take a
    page whose own file fits the budget over it.
    """
    lead = (
        f"generate_llms.py: docs/{md_name} makes llms-{slug}.txt "
        f"{shard_bytes:,} bytes, over the {SHARD_LIMIT_BYTES:,} byte budget of "
        "one fetch, and "
    )
    if not any(_is_h2(section) for section in sections):
        return lead + "it has no H2 heading to cut it at. Divide it under H2 headings."
    name, largest = max(
        (
            (
                section.splitlines()[0].strip()
                if _is_h2(section)
                else "the text before its first H2",
                len(section.encode("utf-8")),
            )
            for section in sections
        ),
        key=lambda pair: pair[1],
    )
    return (
        lead + f"its section {name!r} alone is {largest:,} bytes, more than the "
        f"{room:,} a part has room for. Divide that section under H2 headings of "
        "its own; do not raise SHARD_LIMIT_BYTES."
    )


def _page_parts(
    slug: str, title: str, page: tuple[str, str], *, shard_bytes: int
) -> tuple[str, ...]:
    """A page too long for one fetch, cut at its H2 headings into parts.

    As few parts as fit the budget, as even as the sections allow, each a
    whole shard of its own: the head names every part, and the page's
    attribution opens each one, so a passage read from any part can still be
    cited back. The head grows with the number of parts it lists, so the count
    is settled first and the room each part leaves for the page follows from
    it. A section over the budget by itself cannot be placed in any part, and
    is refused by name rather than cut mid-text; *shard_bytes*, the size of
    the page as one shard, is the size that refusal quotes.
    """
    md_name, route = page
    sections = _sections(_page_text(md_name))
    # The newline that joins a section to the next one counts against it.
    sizes = [len(section.encode("utf-8")) + 1 for section in sections]
    count = 2
    while True:
        head = _render_part(
            slug=slug, title=title, page=page, number=count, count=count, text=""
        )
        room = SHARD_LIMIT_BYTES - len(head.encode("utf-8"))
        if len(sections) < 2 or max(sizes) > room:
            raise SystemExit(
                _oversized_section(
                    slug=slug,
                    md_name=md_name,
                    shard_bytes=shard_bytes,
                    sections=sections,
                    room=room,
                )
            )
        needed = len(_starts(sizes, room))
        if needed <= count:
            break
        count = needed
    starts = [*_balanced_starts(sizes, count, room), len(sections)]
    texts = [
        "\n".join(sections[begin:end]).strip()
        for begin, end in itertools.pairwise(starts)
    ]
    return tuple(
        _render_part(
            slug=slug,
            title=title,
            page=page,
            number=number,
            count=len(texts),
            text=text,
        )
        for number, text in enumerate(texts, start=1)
    )


def _shard_parts(
    slug: str, title: str, pages: list[tuple[str, str]]
) -> tuple[str, ...]:
    """A shard's text: one file, or numbered parts for one page over the budget.

    A shard of several pages over the budget stays whole, for
    :func:`_check_shard_budget` to refuse: those are narrowed by a split that
    follows a grouping of the domain (see ``MANUAL_SPLITS``), never by a cut
    chosen for size. A shard of one page has nothing left to narrow, so the
    page itself is cut, at its own H2 headings.
    """
    text = _shard_text(title, pages)
    shard_bytes = len(text.encode("utf-8"))
    if len(pages) != 1 or shard_bytes <= SHARD_LIMIT_BYTES:
        return (text,)
    return _page_parts(slug, title, pages[0], shard_bytes=shard_bytes)


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


def build_shards() -> dict[str, tuple[str, ...]]:
    """Shard slug -> its text, in one file or, for one long page, in parts."""
    pages = dict(_routes())
    route_to_file = _route_files()
    shards: dict[str, tuple[str, ...]] = {}
    emitted: set[str] = set()

    def emit(slug: str, title: str, routes: list[str]) -> None:
        held = [
            (route_to_file[route], route) for route in routes if route in route_to_file
        ]
        emitted.update(route for _name, route in held)
        shards[slug] = _shard_parts(slug, title, held)

    # Theory used to travel inside the start shard: six mirror pages with
    # eighteen figures pushed llms-start.txt itself over budget. It gets its
    # own shard instead of a cut, since a client after the getting-started
    # page has no reason to also fetch the physics.
    theory = sorted(
        route for route in pages.values() if route.startswith("reference/theory")
    )
    start_overview = ["start"] if "start" in route_to_file else []
    # The migration guide gets the same treatment: one row per 4.0 break, it
    # alone took llms-start.txt over budget, and a client after the
    # getting-started page has no reason to fetch every renamed parameter.
    # When the page alone outgrows the budget it travels in numbered parts
    # (see _page_parts).
    start_routes = [route for route in START_ROUTES if route != UPGRADING_ROUTE]
    emit("start", "start here", [*start_overview, *start_routes])
    if UPGRADING_ROUTE in route_to_file:
        emit("upgrading", UPGRADING_TITLE, [UPGRADING_ROUTE])
    if theory:
        emit("theory", "Theory and reference", theory)

    manual_split_slugs = {
        slug for splits in MANUAL_SPLITS.values() for slug, _label, _leaves in splits
    }
    for slug, routes in _shard_members().items():
        overview = _shard_folders().get(slug, slug)
        # A carved-out shard (see MANUAL_SPLITS) has no overview page of its
        # own; the folder it names already opened its primary shard above.
        include_overview = overview in route_to_file and slug not in manual_split_slugs
        emit(
            slug,
            _shard_label(slug),
            ([overview] if include_overview else []) + routes,
        )

    # The reference pages that are neither theory (its own shard) nor a
    # topic's: today that is the bibliography, which was indexed in llms.txt
    # while its text sat in no shard at all.
    # The API index stays out: llms.txt lists the whole generated reference as
    # Optional, one page per module, and a shard duplicating that table would
    # be the largest file in the set saying the least.
    # The glossary travels on its own. With the bibliography beside it the
    # reference shard reached the fetch budget, and the two answer different
    # questions: a client after the definition of a quantity has no use for the
    # list of sources, nor the other way round.
    reference = sorted(
        route
        for route in pages.values()
        if route.startswith("reference/")
        and not route.startswith(("reference/theory", "reference/api"))
        and route != GLOSSARY_ROUTE
    )
    if reference:
        emit("reference", "Reference", reference)
    if GLOSSARY_ROUTE in route_to_file:
        emit("glossary", "Glossary of quantities", [GLOSSARY_ROUTE])

    # Every mirror page belongs to a shard; a page that falls between the
    # buckets is how the bibliography went missing. The set compared against is
    # what emit() actually consumed, not a second prediction of it: predicting
    # exempted the overview of a subgroup with no guides, which no shard holds.
    allowed_out = {"reference/api"}
    dropped = sorted(set(pages.values()) - emitted - allowed_out)
    if dropped:
        raise SystemExit(
            "generate_llms.py: mirror page(s) in no shard: " + ", ".join(dropped)
        )
    return shards


def build_llms_full(llms_txt: str) -> str:
    parts = [llms_txt, "\n---\n"]
    parts += [_body(name, route) for name, route in _routes()]
    return "\n".join(parts)


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
        for name, _route in _routes()
        if not name.endswith("/index.md")
        and not name.startswith("reference/api")
        and f"({name})" not in readme
    ]
    if missing:
        raise SystemExit(
            "generate_llms.py: docs/README.md does not link " + ", ".join(missing)
        )


def _check_shard_budget(sizes: dict[str, int]) -> None:
    """Fail the run if any shard exceeds :data:`SHARD_LIMIT_BYTES`.

    This used to be a printed note with exit 0, so llms-start.txt and
    llms-buildings-insulation.txt sat over budget for weeks with a green CI: a
    client that truncates at a few hundred kilobytes read a partial shard and
    nothing here ever said so. The budget is not negotiable (see its own
    docstring); the only fix for an oversized shard is a narrower split, never
    a higher SHARD_LIMIT_BYTES. A shard of one page does not reach this check
    over the budget: :func:`_page_parts` has already cut it at its H2
    headings, or refused the section that does not fit any part.
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
        + "\nSplit the area into a narrower shard; do not raise SHARD_LIMIT_BYTES."
    )


def main() -> None:
    _check_areas_cover_the_tree()
    _check_readme_covers_the_mirror()
    version = _version()
    shards = build_shards()
    files = _published(shards)
    llms = build_llms_txt(
        version,
        {slug: _part_names(slug, len(parts)) for slug, parts in shards.items()},
    )
    (ROOT / "llms.txt").write_text(llms, encoding="utf-8")
    (ROOT / "llms-full.txt").write_text(build_llms_full(llms), encoding="utf-8")

    # Remove shards this run no longer produces. Regrouping a section renames
    # its shard, and an orphan left behind would keep serving text that
    # llms.txt no longer indexes, silently and indefinitely. A page cut into
    # parts retires its single file the same way, and the parts it no longer
    # needs. The root-level sweep also retires shards left by the era when
    # they lived next to llms.txt.
    SHARDS_DIR.mkdir(parents=True, exist_ok=True)
    keep = {f"llms-{name}.txt" for name in files}
    for path in SHARDS_DIR.glob("llms-*.txt"):
        if path.name not in keep:
            path.unlink()
            print(f"  removed stale shard llms/{path.name}")
    for path in ROOT.glob("llms-*.txt"):
        if path.name != "llms-full.txt":
            path.unlink()
            print(f"  removed stale shard {path.name}")

    sizes: dict[str, int] = {}
    for name, text in files.items():
        (SHARDS_DIR / f"llms-{name}.txt").write_text(text, encoding="utf-8")
        sizes[name] = len(text.encode("utf-8"))

    print(
        f"llms.txt regenerated (v{version}): {len(_routes())} pages, "
        f"{len(_api_routes())} API pages listed as optional."
    )
    _check_shard_budget(sizes)


if __name__ == "__main__":
    main()
