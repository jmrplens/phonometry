#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The dependency floors pyproject.toml declares, pinned exactly.

Each requirement of the package is a floor, ``name>=version``, and the floor is
measured: it is the oldest release the library's suite passes with, on each
Python the package supports. A floor may be followed by releases above it that
the package refuses, ``name>=version,!=bad``, when one release between the
floor and the newest is broken (svglib 1.4.0 stops at a pdb prompt); the job
still pins the floor. Where a newer Python needs a newer floor, because the
oldest release has no wheel for it, the requirement is written once per
Python with a marker, ``numpy>=2.1.0; python_version=='3.13'``, and the
markers of one distribution give every supported Python exactly one floor.
The minimum-versions job in ``.github/workflows/python-app.yml`` runs on each
supported Python, installs what this script prints for that Python and runs
that suite, so a floor nobody tested cannot sit in the metadata. The pins the
repository develops on (``requirements*.txt``) are a different thing and stay
at the latest releases.

Reading the floors from pyproject.toml rather than from a second list keeps
one source: raising a floor is an edit to pyproject.toml, and the job follows.

Usage::

    python scripts/minimum_requirements.py           # one name==floor per line
    python scripts/minimum_requirements.py --python  # the Python floor, e.g. 3.12
    python scripts/minimum_requirements.py --check   # the installed versions are the floors

The floors printed and checked are those of the Python that runs the script.
The script is stdlib only, since it runs before anything is installed.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: A requirement the job can pin: a name and one lower bound, then any number of
#: single releases above it the package refuses, then at most one marker on the
#: Python version, nothing else. An upper bound, a wildcard or any other clause
#: or marker would leave the floor ambiguous.
_FLOOR = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*>=\s*(?P<version>\d[0-9A-Za-z.]*)"
    r"(?P<excluded>(?:\s*,\s*!=\s*\d+(?:\.\d+)*)*)"
    r"(?:\s*;\s*(?P<marker>\S.*?))?\s*$"
)

#: One excluded release in the tail of :data:`_FLOOR`.
_EXCLUDED = re.compile(r"!=\s*(?P<version>\d+(?:\.\d+)*)")

#: The one marker a floor may carry: the Python version, below, at or from a
#: release. With these three a distribution's floors can split the Pythons
#: into ranges, the last of them open above.
_MARKER = re.compile(
    r"^python_version\s*(?P<operator><|==|>=)\s*"
    r"(?P<quote>['\"])(?P<major>\d+)\.(?P<minor>\d+)(?P=quote)$"
)

#: The Python floor, as requires-python spells it.
_PYTHON_FLOOR = re.compile(r"^>=\s*(?P<version>\d+\.\d+)$")

#: A Python version as its major and minor numbers.
_Python = tuple[int, int]


@dataclass(frozen=True)
class _Floor:
    """One requirement of pyproject.toml, read as a floor."""

    #: The requirement as written.
    spec: str
    #: The distribution name, normalised.
    name: str
    #: The lower bound.
    version: str
    #: The releases above the floor the requirement refuses.
    excluded: tuple[str, ...]
    #: The marker's comparison and the Python it names, or ``None`` for every Python.
    marker: tuple[str, _Python] | None

    def holds_on(self, python: _Python) -> bool:
        """Whether pip applies the requirement on *python*."""
        if self.marker is None:
            return True
        operator, named = self.marker
        if operator == "<":
            return python < named
        if operator == "==":
            return python == named
        return python >= named


def _normalise(name: str) -> str:
    """The distribution name as an index compares it (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _release(version: str, spec: str) -> tuple[int, ...]:
    """*version* as the numbers PEP 440 compares, trailing zeros dropped.

    :raises ValueError: when *version* is not a plain release, which an
        exclusion beside it could not be ordered against.
    """
    if not re.fullmatch(r"\d+(?:\.\d+)*", version):
        msg = (
            f"{spec!r} excludes a release beside the floor {version}, which is "
            "not a plain release number the exclusion can be ordered against."
        )
        raise ValueError(msg)
    numbers = [int(part) for part in version.split(".")]
    while len(numbers) > 1 and numbers[-1] == 0:
        numbers.pop()
    return tuple(numbers)


def _exclusions(spec: str, floor: str, tail: str) -> tuple[str, ...]:
    """The releases *spec* excludes beside its *floor*, each one above it.

    :raises ValueError: for an exclusion of the floor itself, which the job
        would install all the same, or of a release below it, which the floor
        already refuses.
    """
    excluded = tuple(found["version"] for found in _EXCLUDED.finditer(tail))
    if not excluded:
        return excluded
    lowest = _release(floor, spec)
    for version in excluded:
        if _release(version, spec) == lowest:
            msg = (
                f"{spec!r} excludes its own floor: the minimum-versions job "
                "would install a release the requirement refuses."
            )
            raise ValueError(msg)
        if _release(version, spec) < lowest:
            msg = (
                f"{spec!r} excludes {version}, below the floor: it excludes "
                "nothing the floor admits."
            )
            raise ValueError(msg)
    return excluded


def _not_a_floor(spec: str) -> ValueError:
    return ValueError(
        f"{spec!r} is not a floor the minimum-versions job can pin: write one "
        "lower bound, 'name>=version', and nothing else but the releases above "
        "it the package refuses, ',!=version', and at most one marker on the "
        "Python, '; python_version<\"3.13\"', '==' or '>='."
    )


def _read(spec: str) -> _Floor:
    """*spec* as a floor.

    :raises ValueError: for anything but one ``>=`` floor, ``!=`` exclusions
        above it and one marker on ``python_version``, or for an exclusion of
        the floor or of a release below it.
    """
    match = _FLOOR.match(spec.strip())
    if match is None:
        raise _not_a_floor(spec)
    marker = None
    if match["marker"] is not None:
        on_python = _MARKER.match(match["marker"])
        if on_python is None:
            raise _not_a_floor(spec)
        named = (int(on_python["major"]), int(on_python["minor"]))
        marker = (on_python["operator"], named)
    version = match["version"]
    return _Floor(
        spec=spec,
        name=_normalise(match["name"]),
        version=version,
        excluded=_exclusions(spec, version, match["excluded"]),
        marker=marker,
    )


def _python(version: str) -> _Python:
    major, minor = version.split(".")
    return int(major), int(minor)


def _spelt(python: _Python) -> str:
    return f"{python[0]}.{python[1]}"


def _on(read: list[_Floor], python: _Python) -> dict[str, _Floor]:
    """The floor of each distribution on *python*, in the order first declared.

    :raises ValueError: for a distribution with two floors there, or whose
        exclusions two lists spell differently there.
    """
    found: dict[str, _Floor] = {}
    for floor in read:
        if not floor.holds_on(python):
            continue
        first = found.setdefault(floor.name, floor)
        if first.version != floor.version:
            msg = (
                f"{floor.name} has two floors on Python {_spelt(python)}, "
                f"{first.version} and {floor.version}: every list that names it "
                "has to name the same one, and its markers must not overlap."
            )
            raise ValueError(msg)
        if first.excluded != floor.excluded:
            msg = (
                f"{floor.name} excludes {list(first.excluded)} in one list and "
                f"{list(floor.excluded)} in another on Python {_spelt(python)}: "
                "every list that names it has to exclude the same releases."
            )
            raise ValueError(msg)
    return found


def floors(pyproject: dict[str, object], python: str | None = None) -> dict[str, str]:
    """Every dependency and extra of the project on one Python, as ``{name: floor}``.

    The requirements are read for every Python their markers tell apart, not
    only for *python*, so a pyproject.toml that would leave another Python
    without a floor, or with two, fails on whichever Python reads it.

    :param pyproject: The parsed pyproject.toml.
    :param python: The Python, ``"X.Y"``; by default the one running.
    :return: One floor per distribution, in the order first declared.
    :raises ValueError: for a requirement that is not one ``>=`` floor with
        nothing beside it but releases above it it excludes (``!=``) and one
        marker on ``python_version`` (``<``, ``==`` or ``>=`` a release), for
        an exclusion of the floor or of a release below it, for a
        distribution with two floors on one Python or whose exclusions two
        lists spell differently there, for a distribution its markers leave
        without a floor on a Python requires-python admits, and for a
        *python* older than requires-python.
    """
    project = pyproject["project"]
    if not isinstance(project, dict):
        msg = "pyproject.toml has no [project] table."
        raise ValueError(msg)
    specs: list[str] = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        specs += extra
    read = [_read(spec) for spec in specs]
    oldest = _python(python_floor(pyproject)) if "requires-python" in project else None
    wanted = _python(python) if python is not None else sys.version_info[:2]
    if oldest is not None and wanted < oldest:
        msg = (
            f"Python {_spelt(wanted)} is older than the {_spelt(oldest)} "
            "requires-python names: the package has no floors there."
        )
        raise ValueError(msg)
    # Whether a marker holds changes only at the Python it names, so the
    # Pythons on either side of each one stand for every other Python.
    named = {floor.marker[1] for floor in read if floor.marker is not None}
    seen = {
        (major, minor + step)
        for major, minor in named
        for step in (-1, 0, 1)
        if minor + step >= 0
    }
    seen.add(wanted)
    names = list(dict.fromkeys(floor.name for floor in read))
    for each in sorted(seen):
        if oldest is not None and each < oldest:
            continue
        found = _on(read, each)
        for name in names:
            if name not in found:
                msg = (
                    f"{name} has no floor on Python {_spelt(each)}: its markers "
                    "leave that Python out, so the package would ask for no "
                    f"{name} there."
                )
                raise ValueError(msg)
    return {name: floor.version for name, floor in _on(read, wanted).items()}


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

    A local version label is not part of the release: torch from its CPU
    index installs as ``2.x.y+cpu``, which is the floor ``2.x.y`` built
    without CUDA.

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
        if installed.split("+", 1)[0] != version:
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
