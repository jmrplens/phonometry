#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Refuse a release whose wheel or sdist is not the package this commit holds.

The suite imports phonometry from ``src``, where every module and every data
file is always there, so it cannot see a package that loses one on the way to
PyPI: a data directory added without its ``package-data`` glob, a module left
out by a packaging change, a stray file swept into the wheel. Such a release
installs, imports, and fails the first time someone reads the missing table,
and a version number cannot be uploaded twice.

So the artifacts are compared with git, file by file, before anything is
published:

- the build left exactly one sdist and one wheel, named for ``VERSION``, and
  both say that version in their metadata;
- every file git tracks under ``src/phonometry`` is in the wheel, at
  ``phonometry/<path>``, and in the sdist, at ``phonometry-<version>/src/...``;
- the wheel holds nothing else but its ``.dist-info``: no byte-compiled file,
  no test, no second top-level package;
- the sdist carries what building the wheel from it needs: ``pyproject.toml``,
  ``VERSION`` (the version is read from it) and the PyPI readme;
- both declare the licence, ``License-Expression: MIT`` and ``License-File:
  LICENSE`` in their metadata, and both carry the repository's ``LICENSE``
  where PEP 639 puts it, under ``.dist-info/licenses/`` in the wheel and at the
  root of the sdist. ``built_license.py`` reads it, as it does for the
  PyOctaveBand bridge, whose 2.2.0 shipped a licence classifier and no text;
- every file of the sdist that git tracks is one ``.gitattributes`` checks out
  with LF whatever the cloner's ``core.autocrlf`` or ``core.eol``. A clone
  made with ``core.autocrlf`` on writes CRLF into any other text file, on
  Linux and macOS too, and a release rebuilt from it, as SECURITY.md
  describes, would pack bytes PyPI does not hold.
"""

from __future__ import annotations

import argparse
import email.parser
import pathlib
import subprocess  # nosec B404 - git, with fixed arguments
import sys
import tarfile
import zipfile

from built_license import Built, license_problems

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_PACKAGE = "phonometry"
#: What building the wheel from the sdist reads, beside the package itself and
#: the licence files, which :data:`LICENSE_FILES` names.
SDIST_SUPPORT = ("pyproject.toml", "VERSION", "README_PYPI.md")
#: The SPDX expression phonometry declares.
LICENSE_EXPRESSION = "MIT"
#: The licence files it declares, by the path PEP 639 records. Each carries the
#: text of the repository's file of the same name.
LICENSE_FILES = ("LICENSE",)
#: How long a git query may take [s]: it takes well under a second, so the
#: bound only ends a hang.
_GIT_S = 60.0


def tracked_package_files(root: pathlib.Path = _ROOT) -> list[str]:
    """Every file git tracks under ``src/phonometry``, relative to ``src``.

    :param root: The repository checkout.
    :return: Paths such as ``phonometry/building/data/rows.json``, sorted.
    """
    out = subprocess.run(  # nosec B603 B607 - fixed git invocation
        ["git", "-C", str(root), "ls-files", "-z", f"src/{_PACKAGE}"],
        check=True,
        capture_output=True,
        timeout=_GIT_S,
    ).stdout.decode("utf-8")
    return sorted(path.removeprefix("src/") for path in out.split("\0") if path)


def line_ending_problems(
    sdist: pathlib.Path, version: str, root: pathlib.Path = _ROOT
) -> list[str]:
    """The files of the sdist that a checkout could write with CRLF line endings.

    Only the files git tracks are asked about: the ones setuptools writes
    itself (``PKG-INFO``, ``setup.cfg``, the ``.egg-info``) come from no
    checkout.

    :param sdist: The built source distribution.
    :param version: The version being released.
    :param root: The repository checkout whose ``.gitattributes`` is read.
    :return: One sentence per tracked file whose ``eol`` attribute is not
        ``lf``; empty when a checkout anywhere gives every one of them LF.
    """
    top = f"{_PACKAGE}-{version}/"
    with tarfile.open(sdist) as archive:
        carried = sorted(
            member.name.removeprefix(top)
            for member in archive.getmembers()
            if member.isfile() and member.name.startswith(top)
        )
    listed = subprocess.run(  # nosec B603 B607 - fixed git invocation
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
        timeout=_GIT_S,
    ).stdout.decode("utf-8")
    tracked = set(listed.split("\0"))
    checked = [path for path in carried if path in tracked]
    if not checked:
        return []
    answer = subprocess.run(  # nosec B603 B607 - fixed git invocation
        ["git", "-C", str(root), "check-attr", "--stdin", "-z", "eol"],
        check=True,
        capture_output=True,
        timeout=_GIT_S,
        input="\0".join(checked).encode("utf-8"),
    ).stdout.decode("utf-8")
    fields = answer.split("\0")
    eol = {fields[i]: fields[i + 2] for i in range(0, len(fields) - 2, 3)}
    return [
        f"the sdist carries {path}, which .gitattributes does not check out "
        "with LF on every platform"
        for path in checked
        if eol.get(path) != "lf"
    ]


def _metadata_version(raw: bytes) -> str | None:
    return email.parser.BytesParser().parsebytes(raw).get("Version")


def _license_problems(path: pathlib.Path) -> list[str]:
    """What is wrong with the licence a wheel or an sdist declares and carries."""
    try:
        built = Built(path)
    except ValueError as error:
        return [str(error)]
    return license_problems(
        built,
        expression=LICENSE_EXPRESSION,
        files={name: (_ROOT / name).read_bytes() for name in LICENSE_FILES},
        config="pyproject.toml",
    )


def wheel_problems(wheel: pathlib.Path, version: str, tracked: list[str]) -> list[str]:
    """What is wrong with the wheel, one sentence per problem.

    :param wheel: The built wheel.
    :param version: The version being released.
    :param tracked: The package files git tracks, as :func:`tracked_package_files`
        returns them.
    :return: The problems found; empty when the wheel is the package and
        carries its licence.
    """
    dist_info = f"{_PACKAGE}-{version}.dist-info/"
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        metadata = (
            archive.read(f"{dist_info}METADATA")
            if f"{dist_info}METADATA" in names
            else b""
        )
    problems = []
    if not metadata:
        problems.append(f"the wheel has no {dist_info}METADATA")
    else:
        if _metadata_version(metadata) != version:
            problems.append(
                f"the wheel's METADATA says version {_metadata_version(metadata)}, not {version}"
            )
        problems += _license_problems(wheel)
    present = set(names)
    problems += [f"the wheel lacks {path}" for path in tracked if path not in present]
    expected = set(tracked)
    problems += [
        f"the wheel carries {name}, which git does not track under src/{_PACKAGE}"
        for name in sorted(present)
        if not name.startswith(dist_info) and name not in expected
    ]
    return problems


def sdist_problems(sdist: pathlib.Path, version: str, tracked: list[str]) -> list[str]:
    """What is wrong with the sdist, one sentence per problem.

    :param sdist: The built source distribution.
    :param version: The version being released.
    :param tracked: The package files git tracks, as :func:`tracked_package_files`
        returns them.
    :return: The problems found; empty when the sdist can rebuild the wheel
        and carries its licence.
    """
    top = f"{_PACKAGE}-{version}/"
    with tarfile.open(sdist) as archive:
        members = {
            member.name: member for member in archive.getmembers() if member.isfile()
        }
        member = members.get(f"{top}PKG-INFO")
        handle = archive.extractfile(member) if member is not None else None
        pkg_info = handle.read() if handle is not None else b""
    problems = []
    if not pkg_info:
        problems.append(f"the sdist has no {top}PKG-INFO")
    else:
        if _metadata_version(pkg_info) != version:
            problems.append(
                f"the sdist's PKG-INFO says version {_metadata_version(pkg_info)}, not {version}"
            )
        problems += _license_problems(sdist)
    problems += [
        f"the sdist lacks {top}{name}"
        for name in SDIST_SUPPORT
        if f"{top}{name}" not in members
    ]
    problems += [
        f"the sdist lacks {top}src/{path}"
        for path in tracked
        if f"{top}src/{path}" not in members
    ]
    return problems


def dist_problems(
    dist: pathlib.Path,
    version: str,
    tracked: list[str],
    root: pathlib.Path = _ROOT,
) -> list[str]:
    """Every problem with the contents of a build's output directory.

    :param dist: The directory ``python -m build`` wrote to.
    :param version: The version being released.
    :param tracked: The package files git tracks.
    :param root: The repository checkout whose ``.gitattributes`` is read.
    :return: The problems found; empty when the directory holds exactly the
        release's sdist and wheel and both are right.
    """
    sdist = dist / f"{_PACKAGE}-{version}.tar.gz"
    wheel = dist / f"{_PACKAGE}-{version}-py3-none-any.whl"
    found = sorted(path.name for path in dist.iterdir())
    problems = []
    if found != sorted([sdist.name, wheel.name]):
        problems.append(
            f"{dist} holds {found}, not exactly {sdist.name} and {wheel.name}"
        )
    if wheel.is_file():
        problems += wheel_problems(wheel, version, tracked)
    if sdist.is_file():
        problems += sdist_problems(sdist, version, tracked)
        problems += line_ending_problems(sdist, version, root)
    return problems


def main(argv: list[str] | None = None) -> int:
    """Check a build's output directory against git; print each problem found."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "dist", type=pathlib.Path, help="the directory python -m build wrote to"
    )
    parser.add_argument(
        "--version", help="the version being released (default: the VERSION file)"
    )
    args = parser.parse_args(argv)
    version = args.version or (_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    tracked = tracked_package_files()
    problems = dist_problems(args.dist, version, tracked)
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if problems:
        return 1
    print(
        f"The sdist and the wheel of {version} carry the {len(tracked)} files git tracks under src/{_PACKAGE}, and nothing else, declare and carry the {LICENSE_EXPRESSION} licence, and every tracked file of the sdist is checked out with LF everywhere."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
