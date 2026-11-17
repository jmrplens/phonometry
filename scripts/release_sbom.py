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

The tool is run with ``--output-reproducible``, which leaves out the time of
writing and the serial number, so that the document holds nothing of the day
it was made but what pip resolved and what the tool, pinned with everything
it imports in ``requirements-release.txt``, wrote of itself. The serial
number is required all the same by the SBOM attestation the release makes:
``actions/attest-sbom`` takes a CycloneDX document only when ``bomFormat``,
``specVersion`` and ``serialNumber`` are all set, and refused the 4.0.0 SBOM,
which had no serial number, after the files were on PyPI.

The serial number written here is not a random one: it is the name-based
UUID (version 5, of RFC 9562), in the URL namespace, of the package URL
``pkg:pypi/phonometry@<version>`` followed by ``#`` and the SHA-256 of the
finished document without its serial number, written with its keys sorted.
One document of one release always gets the same serial number, so the same
environment described by the same tool gives the same bytes. Another
document gets another one, as the CycloneDX schema asks of every BOM, even
of one release: a rehearsal run again after numpy or scipy published a
release, or a release run again after a failure, describes what pip resolves
that day. Whatever serial number the tool wrote is replaced.

The result is then checked three times. Against ``pyproject.toml``: every
runtime dependency the package declares has to appear, with a version, or the
document describes some other environment than the one a user gets. Against
``requirements-release.txt``: every tool the document says wrote it has to
be there at that version, so a tool that moved on its own is seen before the
document is published. And against what the attestation reads before it
attests anything: a file of at
most 16 MiB, the three fields set, ``bomFormat`` set to ``CycloneDX`` and
the serial number in the form the CycloneDX schema requires. A rehearsal
attests nothing, so this check is the only place where a rehearsal can see
an SBOM the attestation would refuse.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import tomllib
import uuid
from typing import Any

_ROOT = pathlib.Path(__file__).resolve().parent.parent
#: Installer tooling the environment carries that the library does not need.
INSTALLER_COMPONENTS = frozenset({"pip", "setuptools", "wheel"})
#: The form of a serial number, as the CycloneDX 1.6 schema writes it.
SERIAL_NUMBER = re.compile(
    r"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)
#: The largest file the SBOM attestation reads, in bytes: ``MAX_SBOM_SIZE_BYTES``
#: of ``src/sbom.ts`` in ``actions/attest``, which refuses a larger one before
#: it reads a field.
MAX_SBOM_BYTES = 16 * 1024 * 1024
#: The distribution of a tool the SBOM names by another name: ``cyclonedx-bom``
#: writes itself into ``metadata.tools`` as its command, ``cyclonedx-py``.
TOOL_DISTRIBUTIONS = {"cyclonedx-py": "cyclonedx-bom"}


def _normalised(name: str) -> str:
    """``name`` as PEP 503 compares distribution names."""
    return re.sub(r"[-_.]+", "-", name).lower()


def package_url(version: str) -> str:
    """The package URL that names release ``version`` on PyPI.

    :param version: The version being released.
    :return: ``pkg:pypi/phonometry@<version>``.
    """
    return f"pkg:pypi/phonometry@{version}"


def serial_number(sbom: dict[str, Any], version: str) -> str:
    """The serial number of ``sbom``, the SBOM of release ``version``.

    :param sbom: The finished document; a serial number it carries is not
        read.
    :param version: The version being released.
    :return: ``urn:uuid:`` and the version 5 UUID, in the URL namespace of
        RFC 9562, of :func:`package_url`, ``#`` and the SHA-256 of ``sbom``
        without ``serialNumber``, written with its keys sorted: the same for
        one document of one release, different for any other document.
    """
    content = {key: value for key, value in sbom.items() if key != "serialNumber"}
    digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    name = f"{package_url(version)}#{digest}"
    return f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, name)}"


def format_problems(sbom: dict[str, Any]) -> list[str]:
    """What would keep ``actions/attest-sbom`` from attesting ``sbom``.

    :param sbom: A CycloneDX document.
    :return: The problems found; empty when the document says it is
        CycloneDX, names its specification version and carries a serial
        number in the form the schema requires.
    """
    problems = []
    if sbom.get("bomFormat") != "CycloneDX":
        problems.append(
            f"the SBOM gives bomFormat {sbom.get('bomFormat')!r}, not 'CycloneDX'"
        )
    if not sbom.get("specVersion"):
        problems.append("the SBOM gives no specVersion")
    serial = sbom.get("serialNumber")
    if not serial:
        problems.append("the SBOM has no serialNumber")
    elif not isinstance(serial, str) or not SERIAL_NUMBER.fullmatch(serial):
        problems.append(
            f"the SBOM's serialNumber {serial!r} is not urn:uuid: and a UUID"
        )
    return problems


def size_problems(data: bytes) -> list[str]:
    """Whether the SBOM attestation would refuse a file of ``data`` for its size.

    :param data: The bytes of the SBOM file as it is written.
    :return: The problem found; empty when the file is at most
        :data:`MAX_SBOM_BYTES` long.
    """
    if len(data) > MAX_SBOM_BYTES:
        return [
            f"the SBOM is {len(data)} bytes, over the {MAX_SBOM_BYTES} the SBOM"
            " attestation reads"
        ]
    return []


def pinned_tools(
    requirements: pathlib.Path = _ROOT / "requirements-release.txt",
) -> dict[str, str]:
    """The exact pins of the release tooling.

    :param requirements: The requirements file the release installs.
    :return: The version of every ``name==version`` line, by normalised name.
    """
    pins = {}
    for line in requirements.read_text(encoding="utf-8").splitlines():
        name, separator, version = line.split("#", 1)[0].strip().partition("==")
        if separator:
            pins[_normalised(name)] = version.strip()
    return pins


def tool_problems(sbom: dict[str, Any], pins: dict[str, str]) -> list[str]:
    """Which tools ``sbom`` says wrote it that are not the ones pinned.

    :param sbom: A CycloneDX document.
    :param pins: The pinned release tooling (:func:`pinned_tools`).
    :return: The problems found; empty when every tool in
        ``metadata.tools.components`` is pinned at the version it gives.
    """
    problems = []
    tools = sbom.get("metadata", {}).get("tools", {}).get("components", [])
    for tool in tools:
        name, version = tool.get("name", ""), tool.get("version")
        pinned = pins.get(_normalised(TOOL_DISTRIBUTIONS.get(name, name)))
        if pinned is None:
            problems.append(
                f"the SBOM was written by {name} {version}, which"
                " requirements-release.txt does not pin"
            )
        elif pinned != version:
            problems.append(
                f"the SBOM was written by {name} {version}, and"
                f" requirements-release.txt pins {pinned}"
            )
    return problems


def declared_dependencies(
    pyproject: pathlib.Path = _ROOT / "pyproject.toml",
) -> list[str]:
    """The names of the runtime dependencies ``pyproject.toml`` declares.

    A dependency whose floor differs from one Python to another is declared
    once per Python, behind a marker, and is one dependency all the same.

    :param pyproject: The project file.
    :return: The distribution names, lower-cased, without version specifiers,
        each once, in the order first declared.
    """
    with pyproject.open("rb") as handle:
        project = tomllib.load(handle)["project"]
    names = (
        re.split(r"[\s<>=!~;\[]", spec, maxsplit=1)[0].lower()
        for spec in project["dependencies"]
    )
    return list(dict.fromkeys(names))


def finish(sbom: dict[str, Any], version: str, dependencies: list[str]) -> list[str]:
    """Complete ``sbom`` in place for ``version``; return what is wrong with it.

    :param sbom: A CycloneDX document as ``cyclonedx-py`` wrote it.
    :param version: The version being released.
    :param dependencies: The runtime dependencies the package declares.
    :return: The problems found; empty when every declared dependency is
        listed with a version and the SBOM attestation would accept the
        document (:func:`format_problems`). Its size is held to the
        attestation's limit where the file is written (:func:`main`).
    """
    root = sbom["metadata"]["component"]
    root["version"] = version
    root["purl"] = package_url(version)
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
    sbom["serialNumber"] = serial_number(sbom, version)
    return format_problems(sbom) + problems


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
    problems += tool_problems(sbom, pinned_tools())
    data = (json.dumps(sbom, indent=2) + "\n").encode("utf-8")
    problems += size_problems(data)
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if problems:
        return 1
    args.sbom.write_bytes(data)
    listed = ", ".join(f"{c['name']} {c.get('version')}" for c in sbom["components"])
    print(f"SBOM of phonometry {version}: {listed}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
