#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Check that the phonometry a fresh environment installed is the one being released.

The release builds one wheel and installs it, with every optional extra, on
each operating system and Python version the project supports, before it
uploads anything. This is the first thing that runs there. It answers three
questions the suite cannot, because the suite imports from ``src``:

- is the phonometry Python imports the installed one, not the checkout's
  ``src`` tree, and is it the version being released;
- does every module of the installed package import on this platform, with
  the dependency versions pip resolved here;
- is every data file git tracks under ``src/phonometry`` readable through the
  installed package.

The conformance report runs next, against the same installation.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.resources
import pathlib
import pkgutil
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from check_release_artifacts import tracked_package_files


def problems(version: str, tracked: list[str]) -> tuple[list[str], int]:
    """Everything wrong with the installed package, and how many modules it has.

    :param version: The version being released.
    :param tracked: The package files git tracks, relative to ``src``.
    :return: The problems found, and the number of modules imported.
    """
    import phonometry

    found: list[str] = []
    location = pathlib.Path(phonometry.__file__).resolve()
    if (_ROOT / "src") in location.parents:
        found.append(
            f"phonometry was imported from the checkout ({location}), not from the installed wheel"
        )
    if phonometry.__version__ != version:
        found.append(
            f"the installed phonometry is version {phonometry.__version__}, not {version}"
        )
    count = 0
    for module in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        count += 1
        try:
            importlib.import_module(module.name)
        # Every failure is reported, none is expected.
        except Exception as exc:
            found.append(f"{module.name} does not import: {type(exc).__name__}: {exc}")
    package = importlib.resources.files("phonometry")
    for path in tracked:
        relative = path.removeprefix("phonometry/")
        if relative.endswith(".py"):
            continue
        if not package.joinpath(relative).is_file():
            found.append(f"the installed package has no {relative}")
    return found, count


def main(argv: list[str] | None = None) -> int:
    """Check the installed package; print each problem found."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--version", help="the version being released (default: the VERSION file)"
    )
    args = parser.parse_args(argv)
    version = args.version or (_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    tracked = tracked_package_files()
    found, count = problems(version, tracked)
    for problem in found:
        print(f"::error::{problem}", file=sys.stderr)
    if found:
        return 1
    data = sum(not path.endswith(".py") for path in tracked)
    print(
        f"phonometry {version} is installed, its {count} modules import and its "
        f"{data} data files are readable on Python {sys.version.split()[0]} ({sys.platform})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
