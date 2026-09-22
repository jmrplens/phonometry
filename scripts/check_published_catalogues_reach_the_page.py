#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every published catalogue reaches the page that publishes catalogues.

A ``PUBLISHED_*`` mapping is rows this library read off a printed page and
kept. The page at ``/reference/catalogues/`` exists to show them, and
``scripts/generate_catalogue_data.py`` is what carries them there. Nothing
made the two agree, so a catalogue could be written, tested, documented in the
API reference and still be invisible to every reader who is not reading Python:
the rows are in the package, the page does not know they exist, and no gate
says so.

That is not hypothetical. When this guard was first run it found six, and two
of them were years old rather than new: the resilient layers, which is the
thinnest class the library holds and therefore the one a reader is most likely
to go looking for, and the published air conditions. Four more had just been
added by the wave of work that prompted this file. Each one had passed every
other gate.

**What it checks.** Every public ``PUBLISHED_*`` mapping reachable by walking
the imported package has to be named in the generator. The walk is over the
package as it imports rather than over the source text, for the same reason
``check_parameter_units.py`` walks the imported tree: a name assembled at
import, re-exported from a parent package or moved between modules is still a
name a caller can reach, and a grep over files would miss it.

**What it deliberately does not check**, so that the message stays honest: not
that the section renders, not that its prose exists in both languages, and not
that the columns are the right ones. Those are the page's own business and the
site build already fails on a broken page. This guard answers one question,
which nothing else was answering: is there a catalogue the page has never
heard of.

Exit status 0 when every catalogue reaches the page, 1 otherwise.
"""

from __future__ import annotations

import importlib
import pathlib
import pkgutil
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_GENERATOR = _ROOT / "scripts" / "generate_catalogue_data.py"

#: Mappings that are deliberately not on the page, with the reason. A name
#: lands here only when showing it would mislead, never because registering it
#: is work: the point of the guard is that the work gets done.
EXEMPT: dict[str, str] = {}


def published_names() -> dict[str, str]:
    """Every public ``PUBLISHED_*`` mapping, to the module that defines it."""
    sys.path.insert(0, str(_ROOT / "src"))
    import phonometry

    found: dict[str, str] = {}
    for info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if "._" in info.name:
            continue
        try:
            module = importlib.import_module(info.name)
        except Exception:  # noqa: BLE001 - an unimportable module is another gate's
            continue
        for name in dir(module):
            if not name.startswith("PUBLISHED_"):
                continue
            # The deepest module wins, because that is where the rows live.
            # ``walk_packages`` is a prefix walk, so a parent package that
            # re-exports a catalogue is yielded before the module that defines
            # it, and keeping the first would point the report at an
            # ``__init__`` instead of at the file a reader has to open.
            previous = found.get(name)
            if previous is None or info.name.count(".") > previous.count("."):
                found[name] = info.name
    return found


def _is_named(name: str, generator: str) -> bool:
    """Whether *generator* names this catalogue, rather than merely contains it.

    A plain substring test passes on a prefix. ``PUBLISHED_AIR`` is inside
    ``PUBLISHED_AIR_CONDITION``, ``PUBLISHED_ABSORPTION`` inside
    ``PUBLISHED_ABSORPTION_AREAS`` and ``PUBLISHED_TRANSMISSION_LOSS`` inside
    ``PUBLISHED_DUCT_TRANSMISSION_LOSS``, all of which are in the tree today,
    so a catalogue added under any of those shorter names would have been
    reported as reaching a page that had never heard of it. That is the one
    question this file exists to answer, so the match is on whole words.
    """
    return re.search(rf"\b{re.escape(name)}\b", generator) is not None


def main() -> int:
    """Report every catalogue the catalogues page has never heard of."""
    generator = _GENERATOR.read_text(encoding="utf-8")
    missing = {
        name: module
        for name, module in sorted(published_names().items())
        if not _is_named(name, generator) and name not in EXEMPT
    }
    if missing:
        print(
            f"{len(missing)} published catalogue(s) never reach "
            "/reference/catalogues/:",
            file=sys.stderr,
        )
        for name, module in missing.items():
            print(f"  {name}  <- {module}", file=sys.stderr)
        print(
            "  -> add each one to scripts/generate_catalogue_data.py with its "
            "columns, give it a section in both languages of "
            "site/src/content/docs/reference/catalogues.mdx, and add its key to "
            "the catalogue union in site/src/components/Catalogues.astro. A "
            "catalogue nobody can see is a catalogue nobody has.",
            file=sys.stderr,
        )
        return 1
    total = len(published_names())
    print(f"All {total} published catalogues reach /reference/catalogues/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
