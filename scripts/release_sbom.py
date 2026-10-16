#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Finish the software bill of materials of a release and check what it says.

``cyclonedx-py environment`` describes a virtual environment the release
created with nothing in it but the built wheel, so its components are exactly
what ``pip install phonometry`` resolved on the day of the release: numpy,
scipy and whatever they pull in, at the versions pip chose. Two things it
cannot know are filled in here. The root component's version is dynamic in
``pyproject.toml`` (it is read from ``VERSION`` at build time), so the tool
leaves it blank; it is set, with the package URL that names the release on
PyPI. And the environment's own installer is not a dependency of the library,
so a ``pip``, ``setuptools`` or ``wheel`` component is dropped.

The result is then checked against ``pyproject.toml``: every runtime
dependency the package declares has to appear, with a version, or the
document describes some other environment than the one a user gets.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tomllib
from typing import Any

_ROOT = pathlib.Path(__file__).resolve().parent.parent
#: Installer tooling the environment carries that the library does not need.
INSTALLER_COMPONENTS = frozenset({"pip", "setuptools", "wheel"})


def declared_dependencies(
    pyproject: pathlib.Path = _ROOT / "pyproject.toml",
) -> list[str]:
    """The names of the runtime dependencies ``pyproject.toml`` declares.

    :param pyproject: The project file.
    :return: The distribution names, lower-cased, without version specifiers.
    """
    with pyproject.open("rb") as handle:
        project = tomllib.load(handle)["project"]
    return [
        re.split(r"[\s<>=!~;\[]", spec, maxsplit=1)[0].lower()
        for spec in project["dependencies"]
    ]


def finish(sbom: dict[str, Any], version: str, dependencies: list[str]) -> list[str]:
    """Complete ``sbom`` in place for ``version``; return what is wrong with it.

    :param sbom: A CycloneDX document as ``cyclonedx-py`` wrote it.
    :param version: The version being released.
    :param dependencies: The runtime dependencies the package declares.
    :return: The problems found; empty when every declared dependency is
        listed with a version.
    """
    root = sbom["metadata"]["component"]
    root["version"] = version
    root["purl"] = f"pkg:pypi/phonometry@{version}"
    sbom["components"] = [
        component
        for component in sbom.get("components", [])
        if component.get("name", "").lower() not in INSTALLER_COMPONENTS
    ]
    listed = {
        component["name"].lower(): component.get("version")
        for component in sbom["components"]
    }
    problems = [
        f"the SBOM does not list {name}, which phonometry depends on"
        for name in dependencies
        if name not in listed
    ]
    problems += [
        f"the SBOM lists {name} without a version"
        for name in dependencies
        if name in listed and not listed[name]
    ]
    return problems


def main(argv: list[str] | None = None) -> int:
    """Finish an SBOM file in place; print each problem found."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "sbom", type=pathlib.Path, help="the CycloneDX JSON cyclonedx-py wrote"
    )
    parser.add_argument(
        "--version", help="the version being released (default: the VERSION file)"
    )
    args = parser.parse_args(argv)
    version = args.version or (_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    sbom = json.loads(args.sbom.read_text(encoding="utf-8"))
    problems = finish(sbom, version, declared_dependencies())
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if problems:
        return 1
    args.sbom.write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
    listed = ", ".join(f"{c['name']} {c.get('version')}" for c in sbom["components"])
    print(f"SBOM of phonometry {version}: {listed}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
