#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The dependency floors pyproject.toml declares, pinned exactly.

Each requirement of the package is a floor, ``name>=version``, and the floor is
measured: it is the oldest release the library's suite passes with on the
oldest Python the package supports. The minimum-versions job in
``.github/workflows/python-app.yml`` installs what this script prints and runs
that suite, so a floor nobody tested cannot sit in the metadata. The pins the
repository develops on (``requirements*.txt``) are a different thing and stay
at the latest releases.

Reading the floors from pyproject.toml rather than from a second list keeps
one source: raising a floor is an edit to pyproject.toml, and the job follows.

Usage::

    python scripts/minimum_requirements.py           # one name==floor per line
    python scripts/minimum_requirements.py --python  # the Python floor, e.g. 3.12
    python scripts/minimum_requirements.py --check   # the installed versions are the floors

The script is stdlib only, since it runs before anything is installed.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: A requirement the job can pin: a name and one lower bound, nothing else. An
#: upper bound, a marker or a second clause would leave the floor ambiguous.
_FLOOR = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*>=\s*(?P<version>\d[0-9A-Za-z.]*)$"
)

#: The Python floor, as requires-python spells it.
_PYTHON_FLOOR = re.compile(r"^>=\s*(?P<version>\d+\.\d+)$")


def _normalise(name: str) -> str:
    """The distribution name as an index compares it (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def floors(pyproject: dict[str, object]) -> dict[str, str]:
    """Every dependency and extra of the project, as ``{name: floor}``.

    :param pyproject: The parsed pyproject.toml.
    :return: One floor per distribution, in the order first declared.
    :raises ValueError: for a requirement that is not one ``>=`` floor, or a
        distribution whose floor two lists spell differently.
    """
    project = pyproject["project"]
    if not isinstance(project, dict):
        msg = "pyproject.toml has no [project] table."
        raise ValueError(msg)
    specs: list[str] = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        specs += extra
    found: dict[str, str] = {}
    for spec in specs:
        match = _FLOOR.match(spec.strip())
        if match is None:
            msg = (
                f"{spec!r} is not a floor the minimum-versions job can pin: "
                "write one lower bound, 'name>=version', and nothing else."
            )
            raise ValueError(msg)
        name, version = _normalise(match["name"]), match["version"]
        if found.setdefault(name, version) != version:
            msg = (
                f"{name} has two floors, {found[name]} and {version}: every list "
                "that names it has to name the same one."
            )
            raise ValueError(msg)
    return found


def python_floor(pyproject: dict[str, object]) -> str:
    """The oldest Python the package supports, from requires-python.

    :raises ValueError: when requires-python is not one ``>=X.Y`` floor.
    """
    project = pyproject["project"]
    spec = project.get("requires-python", "") if isinstance(project, dict) else ""
    match = _PYTHON_FLOOR.match(str(spec).strip())
    if match is None:
        msg = f"requires-python {spec!r} is not one '>=X.Y' floor."
        raise ValueError(msg)
    return match["version"]


def mismatches(expected: dict[str, str]) -> list[str]:
    """The floors the running environment did not install exactly.

    :param expected: ``{name: floor}``, as :func:`floors` returns it.
    :return: One line per distribution that is missing or at another version.
    """
    problems: list[str] = []
    for name, version in expected.items():
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            problems.append(f"{name}: not installed, the floor is {version}")
            continue
        if installed != version:
            problems.append(f"{name}: {installed} installed, the floor is {version}")
    return problems


def _load(path: Path) -> dict[str, object]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def main(argv: list[str] | None = None) -> int:
    """Print the floors, the Python floor, or check the environment against them."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--pyproject", type=Path, default=ROOT / "pyproject.toml")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--python", action="store_true", help="print the Python floor")
    group.add_argument(
        "--check", action="store_true", help="fail unless the floors are installed"
    )
    args = parser.parse_args(argv)
    pyproject = _load(args.pyproject)
    try:
        if args.python:
            print(python_floor(pyproject))
            return 0
        expected = floors(pyproject)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.check:
        problems = mismatches(expected)
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        if problems:
            return 1
        print(f"OK: {len(expected)} distributions at their floors")
        return 0
    for name, version in expected.items():
        print(f"{name}=={version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
