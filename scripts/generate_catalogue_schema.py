#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Write the JSON Schema of a catalogue document for the documentation site.

``phonometry.io.catalogue_schema`` writes the schema of a catalogue file from
the row classes it is given, and the site publishes the one that covers every
row class the library publishes, so an editor pointed at it completes a
catalogue file of any of them while it is typed. The file is served as it is
from ``site/public/schemas/``, named after the layout version it describes,
because a later layout is a new file beside it rather than a new content
under the same name.

The row classes are found by walking what the package publishes, the same
walk the reader's guards make, so a row class added to any package reaches
the schema without anybody listing it here. CI runs the ``--check`` form and
fails when the committed file is not what a fresh run writes, which is what
keeps a field added to a row class from being missing in every editor.

Run through ``make catalogue-schema``.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import pathlib
import pkgutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import phonometry  # noqa: E402
from phonometry import io  # noqa: E402
from phonometry.io._catalogue import CATALOGUE_SCHEMA_VERSION  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
#: Where the site serves the schema from, beside its other static files.
OUTPUT = (
    ROOT
    / "site"
    / "public"
    / "schemas"
    / f"phonometry-catalogue-{CATALOGUE_SCHEMA_VERSION}.json"
)


def published_row_classes() -> list[type[io.CatalogueRow]]:
    """Every row class a public package exports, the bases included, by name.

    Keyed by where each class is defined, so two classes that share a name
    both reach :func:`phonometry.io.catalogue_schema`, which refuses them.
    """
    found: dict[str, type[io.CatalogueRow]] = {}
    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.name.startswith("_") or not module.ispkg:
            continue
        package = importlib.import_module(f"phonometry.{module.name}")
        for name in getattr(package, "__all__", ()):
            value = getattr(package, name)
            if inspect.isclass(value) and issubclass(value, io.CatalogueRow):
                found[f"{value.__module__}.{value.__qualname__}"] = value
    return sorted(found.values(), key=lambda cls: cls.__name__)


def render() -> str:
    """The schema file's text, as a fresh run writes it."""
    schema = io.catalogue_schema(*published_row_classes())
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write the schema, or check that the committed one is current.

    :param argv: Command line, for the tests.
    :return: The process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero when the committed file differs from a fresh run",
    )
    args = parser.parse_args(argv)
    fresh = render()
    if args.check:
        held = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if held != fresh:
            print(
                f"{OUTPUT.relative_to(ROOT)} is stale; run `make catalogue-schema`.",
                file=sys.stderr,
            )
            return 1
        print(f"{OUTPUT.name} is current.")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(fresh, encoding="utf-8")
    print(
        f"wrote {OUTPUT.relative_to(ROOT)} ({len(published_row_classes())} row classes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
